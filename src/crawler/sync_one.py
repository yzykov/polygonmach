import argparse
import asyncio

from playwright.async_api import async_playwright

from .browser import open_page
from .config import SETTINGS
from .parser import discover_categories
from .r2_storage import R2Storage
from .site_bundle import (
    SITE_BUNDLE_KEY,
    bundle_data,
    bundle_entity_map,
    bundle_source_hash,
    bundle_sources,
    bundle_index,
    update_site_bundle_entity,
)
from .sync import (
    LANGUAGES,
    parse_language_source,
    save_entity_data,
    save_source,
    sync_entity_images,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Refresh exactly one Polygonmach category or product. "
            "index/site.json is updated incrementally; no full R2 scan."
        )
    )

    entity = parser.add_mutually_exclusive_group(required=True)
    entity.add_argument(
        "--category",
        type=int,
        help="Polygonmach category source_id, e.g. 10",
    )
    entity.add_argument(
        "--product",
        type=int,
        help="Polygonmach product source_id, e.g. 118",
    )

    parser.add_argument(
        "--language",
        choices=LANGUAGES,
        help=(
            "Refresh only one language. By default refresh all languages "
            "whose source URL is already known in index/site.json."
        ),
    )
    parser.add_argument(
        "--url",
        help=(
            "Exact Polygonmach source URL override. Use together with "
            "--language."
        ),
    )

    return parser.parse_args()


async def discover_category_url(
    page,
    source_id: int,
    language: str,
) -> str | None:
    home_url = f"{SETTINGS.source_base_url}/{language}"

    if not await open_page(page, home_url):
        return None

    categories = await discover_categories(page, language)
    return categories.get(source_id)


def source_url_from_record(
    record: dict | None,
    language: str,
) -> str | None:
    sources = bundle_sources(record)
    source = sources.get(language)

    if isinstance(source, dict) and source.get("source_url"):
        return str(source["source_url"])

    data = bundle_data(record)

    if isinstance(data, dict):
        source_meta = data.get("sources")

        if isinstance(source_meta, dict):
            meta = source_meta.get(language)

            if isinstance(meta, dict) and meta.get("source_url"):
                return str(meta["source_url"])

    if language == "ru" and isinstance(record, dict):
        content = record.get("content")

        if isinstance(content, dict) and content.get("source_url"):
            return str(content["source_url"])

    return None


async def main() -> None:
    args = parse_args()

    if args.url and not args.language:
        raise SystemExit("--url requires --language")

    if args.category is not None:
        entity_type = "category"
        kind = "categories"
        source_id = args.category
    else:
        entity_type = "product"
        kind = "products"
        source_id = args.product

    storage = R2Storage()

    # Exactly one bundle read. No hidden fallback to a complete R2 scan.
    loaded_bundle = storage.get_json(SITE_BUNDLE_KEY)

    if not isinstance(loaded_bundle, dict):
        raise SystemExit(
            "index/site.json is missing. Run "
            "`python -m src.crawler.build_site_bundle` once first."
        )

    old_entities = bundle_entity_map(loaded_bundle, kind)
    old_record = old_entities.get(str(source_id))
    old_data = bundle_data(old_record)
    stored_sources = bundle_sources(old_record)

    if args.language:
        languages = (args.language,)
    else:
        known_languages = tuple(
            language
            for language in LANGUAGES
            if source_url_from_record(old_record, language)
        )
        languages = known_languages or LANGUAGES

    parsed_sources: dict[str, dict] = {}

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=SETTINGS.headless,
        )

        context = await browser.new_context(
            locale="ru-RU",
            viewport={"width": 1920, "height": 1080},
        )

        page = await context.new_page()

        try:
            for language in languages:
                url = (
                    args.url
                    if args.language == language
                    else None
                )

                if not url:
                    url = source_url_from_record(
                        old_record,
                        language,
                    )

                if not url and entity_type == "category":
                    url = await discover_category_url(
                        page,
                        source_id,
                        language,
                    )

                if not url:
                    print(
                        f"[{language}] source URL not found; "
                        f"use --language {language} --url <url>"
                    )
                    continue

                print(
                    f"[{entity_type.upper()} {source_id} {language}] "
                    f"{url}"
                )

                source = await parse_language_source(
                    page=page,
                    entity_type=entity_type,
                    language=language,
                    url=url,
                    expected_source_id=source_id,
                )

                if source is None:
                    print(f"  {language}: parse failed")
                    continue

                parsed_sources[language] = source

                stored_source, changed = await save_source(
                    storage=storage,
                    kind=kind,
                    source=source,
                    old_source_hash=bundle_source_hash(
                        old_record,
                        language,
                    ),
                    old_source=stored_sources.get(language),
                )
                stored_sources[language] = stored_source

                if entity_type == "product":
                    extra = f"; tabs={len(source.get('tabs', []))}"
                else:
                    extra = (
                        f"; categories={len(source.get('category_ids', []))}"
                        f"; products={len(source.get('product_ids', []))}"
                    )

                print(
                    f"  {language}: "
                    f"{'CHANGED' if changed else 'unchanged'}"
                    f"{extra}"
                )

            if not parsed_sources:
                raise SystemExit("No source was updated")

            images = await sync_entity_images(
                storage=storage,
                kind=kind,
                source_id=source_id,
                sources=parsed_sources,
                old_data=old_data,
            )

            data, data_changed = await save_entity_data(
                storage=storage,
                kind=kind,
                source_id=source_id,
                sources=parsed_sources,
                images=images,
                old_data=old_data,
            )

            bundle, bundle_changed = update_site_bundle_entity(
                storage=storage,
                kind=kind,
                source_id=source_id,
                source_overrides=stored_sources,
                data_override=data,
                old_bundle=loaded_bundle,
            )

            index_key = f"index/{kind}.json"
            index_changed = storage.put_json_if_changed(
                index_key,
                bundle_index(bundle, kind),
                old_data=bundle_index(loaded_bundle, kind),
            )

        finally:
            await browser.close()

    print()
    print("========== TARGETED SYNC DONE ==========")
    print(f"Entity:       {entity_type}/{source_id}")
    print(
        "data.json:    "
        f"{'CHANGED' if data_changed else 'unchanged'}"
    )
    print(
        "site bundle:  "
        f"{'CHANGED' if bundle_changed else 'unchanged'}"
    )
    print(
        "entity index: "
        f"{'CHANGED' if index_changed else 'unchanged'}"
    )
    print(f"routes:       {len(bundle.get('routes', []))}")
    print("Full R2 scan: NO")


if __name__ == "__main__":
    asyncio.run(main())
