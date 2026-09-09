import asyncio
from datetime import datetime, timezone

from playwright.async_api import async_playwright

from .browser import open_page, polite_delay
from .config import SETTINGS
from .image_sync import sync_images
from .parser import discover_categories, extract_source
from .r2_storage import R2Storage
from .site_bundle import (
    SITE_BUNDLE_KEY,
    build_site_bundle_from_memory,
    bundle_data,
    bundle_entity_map,
    bundle_index,
    bundle_localizations,
    bundle_source_hash,
    bundle_sources,
    localization_snapshot,
    make_site_record,
)


LANGUAGES = ("ru", "tr")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def source_key(kind: str, source_id: int, language: str) -> str:
    return f"{kind}/{source_id}/source/{language}.json"


def data_key(kind: str, source_id: int) -> str:
    return f"{kind}/{source_id}/data.json"


async def discover_all_categories(page) -> dict[str, dict[int, str]]:
    result: dict[str, dict[int, str]] = {}

    for language in LANGUAGES:
        url = f"{SETTINGS.source_base_url}/{language}"
        print(f"[DISCOVERY {language}] {url}")

        if not await open_page(page, url):
            result[language] = {}
            continue

        result[language] = await discover_categories(page, language)
        print(f"  categories: {len(result[language])}")
        await polite_delay()

    return result


async def parse_language_source(
    page,
    entity_type: str,
    language: str,
    url: str,
    expected_source_id: int,
) -> dict | None:
    if not await open_page(page, url):
        return None

    source = await extract_source(page, entity_type, language)

    if source is None:
        return None

    if source["source_id"] != expected_source_id:
        print(
            f"  source_id mismatch [{language}]: "
            f"expected {expected_source_id}, got {source['source_id']}"
        )
        return None

    return source


def clean_source_for_storage(source: dict) -> dict:
    return {
        key: value
        for key, value in source.items()
        if not key.startswith("_") and key != "source_images"
    }


async def save_source(
    storage: R2Storage,
    kind: str,
    source: dict,
    old_source_hash: str | None = None,
    old_source: dict | None = None,
) -> tuple[dict, bool]:
    """
    Persist one parsed language source.

    Normal full sync passes old_source_hash from index/site.json, so this
    function does not need a GET of source/<language>.json before every PUT.
    """
    source_id = source["source_id"]
    language = source["language"]
    key = source_key(kind, source_id, language)
    clean_source = clean_source_for_storage(source)

    if old_source_hash == clean_source.get("source_hash"):
        if isinstance(old_source, dict):
            return old_source, False
        return clean_source, False

    clean_source["updated_at"] = utc_now()
    storage.put_json(key, clean_source)
    return clean_source, True


def preferred_image_urls(sources: dict[str, dict]) -> list[str]:
    ru_source = sources.get("ru")
    tr_source = sources.get("tr")

    if ru_source and ru_source.get("source_images"):
        urls = ru_source["source_images"]
    elif tr_source and tr_source.get("source_images"):
        urls = tr_source["source_images"]
    else:
        urls = []

    return list(dict.fromkeys(urls))


async def sync_entity_images(
    storage: R2Storage,
    kind: str,
    source_id: int,
    sources: dict[str, dict],
    old_data: dict | None,
) -> list[dict]:
    source_urls = preferred_image_urls(sources)

    old_images = (
        old_data.get("images", [])
        if isinstance(old_data, dict)
        else []
    )

    old_by_source = {
        image["source_url"]: image
        for image in old_images
        if isinstance(image, dict) and image.get("source_url")
    }

    old_source_urls = list(old_by_source)

    if source_urls == old_source_urls:
        print("  images: skipped (same source URLs)")
        return old_images

    if all(url in old_by_source for url in source_urls):
        print(
            f"  images: reused existing "
            f"({len(old_images)} -> {len(source_urls)})"
        )
        return [old_by_source[url] for url in source_urls]

    if not source_urls:
        print("  images: none")
        return []

    print(
        f"  images: sync required "
        f"({len(old_source_urls)} -> {len(source_urls)})"
    )

    return await sync_images(
        storage=storage,
        kind=kind,
        source_id=source_id,
        source_urls=source_urls,
        old_images=old_images,
    )


async def save_entity_data(
    storage: R2Storage,
    kind: str,
    source_id: int,
    sources: dict[str, dict],
    images: list[dict],
    old_data: dict | None = None,
) -> tuple[dict, bool]:
    """
    Persist data.json without rereading it from R2 when old_data was already
    loaded from index/site.json.
    """
    key = data_key(kind, source_id)

    source_meta = (
        dict(old_data.get("sources", {}))
        if isinstance(old_data, dict)
        else {}
    )

    for language in LANGUAGES:
        source = sources.get(language)

        if not source:
            continue

        source_meta[language] = {
            "source_url": source["source_url"],
            "source_hash": source["source_hash"],
        }

    data = {
        "source_id": source_id,
        "sources": source_meta,
        "images": images,
    }

    if isinstance(old_data, dict):
        comparable_old = {
            "source_id": old_data.get("source_id"),
            "sources": old_data.get("sources", {}),
            "images": old_data.get("images", []),
        }

        if comparable_old == data:
            return old_data, False

    data["updated_at"] = utc_now()
    storage.put_json(key, data)
    return data, True


def make_index_item_from_record(record: dict) -> dict:
    index = record.get("index")

    if not isinstance(index, dict):
        raise RuntimeError("Site record has no index")

    return {
        "source_id": int(index["source_id"]),
        "title": str(index.get("title", "")),
        "main_image": index.get("main_image"),
    }


def old_record_for(
    old_entities: dict[str, dict],
    source_id: int,
) -> dict | None:
    value = old_entities.get(str(source_id))
    return value if isinstance(value, dict) else None


def old_bundle_source_hash(
    old_record: dict | None,
    language: str,
) -> str | None:
    return bundle_source_hash(old_record, language)


async def main() -> None:
    storage = R2Storage()

    # This is the only normal full-sync R2 read needed to rebuild site.json.
    # It gives us previous source hashes, data/images, localization snapshots
    # and the old site bundle for comparison.
    old_bundle_raw = storage.get_json(SITE_BUNDLE_KEY)
    old_bundle = old_bundle_raw if isinstance(old_bundle_raw, dict) else None

    if old_bundle is None:
        print(
            "WARNING: index/site.json is missing. Full sync will bootstrap "
            "from the supplier without scanning all R2 entity JSON files."
        )
        print(
            "If you already have manual localization/*.json files that must "
            "be imported, run `python -m src.crawler.build_site_bundle` once "
            "before the normal sync."
        )

    old_categories = bundle_entity_map(old_bundle, "categories")
    old_products = bundle_entity_map(old_bundle, "products")

    category_records: dict[str, dict] = {}
    product_records: dict[str, dict] = {}
    category_index: list[dict] = []
    product_index: list[dict] = []

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
            category_urls = await discover_all_categories(page)

            category_ids = sorted(
                set(category_urls.get("ru", {}))
                | set(category_urls.get("tr", {}))
            )

            print()
            print(f"Unique categories: {len(category_ids)}")
            print()

            product_urls: dict[str, dict[int, str]] = {
                "ru": {},
                "tr": {},
            }

            for number, source_id in enumerate(category_ids, start=1):
                print(
                    f"[CATEGORY {number}/{len(category_ids)}] "
                    f"{source_id}"
                )

                old_record = old_record_for(old_categories, source_id)
                parsed_sources: dict[str, dict] = {}
                stored_sources = bundle_sources(old_record)

                for language in LANGUAGES:
                    url = category_urls.get(language, {}).get(source_id)

                    if not url:
                        continue

                    source = await parse_language_source(
                        page=page,
                        entity_type="category",
                        language=language,
                        url=url,
                        expected_source_id=source_id,
                    )

                    if source is None:
                        await polite_delay()
                        continue

                    parsed_sources[language] = source
                    product_urls[language].update(
                        source.get("_product_urls", {})
                    )

                    stored_source, changed = await save_source(
                        storage=storage,
                        kind="categories",
                        source=source,
                        old_source_hash=old_bundle_source_hash(
                            old_record,
                            language,
                        ),
                        old_source=stored_sources.get(language),
                    )
                    stored_sources[language] = stored_source

                    print(
                        f"  {language}: "
                        f"{'CHANGED' if changed else 'unchanged'}"
                    )
                    await polite_delay()

                if not parsed_sources:
                    if old_record is not None:
                        print("  parse failed; keeping previous site record")
                        category_records[str(source_id)] = old_record
                        category_index.append(
                            make_index_item_from_record(old_record)
                        )
                    continue

                old_data = bundle_data(old_record)

                images = await sync_entity_images(
                    storage=storage,
                    kind="categories",
                    source_id=source_id,
                    sources=parsed_sources,
                    old_data=old_data,
                )

                data, data_changed = await save_entity_data(
                    storage=storage,
                    kind="categories",
                    source_id=source_id,
                    sources=parsed_sources,
                    images=images,
                    old_data=old_data,
                )

                if data_changed:
                    print("  data.json: CHANGED")
                else:
                    print("  data.json: unchanged")

                localizations = bundle_localizations(old_record)
                ru_localization = localization_snapshot(
                    storage=storage,
                    kind="categories",
                    source_id=source_id,
                    old_record=old_record,
                    language="ru",
                )

                if isinstance(ru_localization, dict):
                    localizations["ru"] = ru_localization

                record = make_site_record(
                    source_id=source_id,
                    sources=stored_sources,
                    localizations=localizations,
                    data=data,
                )

                if record is None:
                    print("  site record build failed")
                    continue

                category_records[str(source_id)] = record
                category_index.append(
                    make_index_item_from_record(record)
                )

            category_index.sort(key=lambda item: item["source_id"])
            category_index_changed = storage.put_json_if_changed(
                "index/categories.json",
                category_index,
                old_data=bundle_index(old_bundle, "categories"),
            )
            print(
                "index/categories.json: "
                f"{'CHANGED' if category_index_changed else 'unchanged'}"
            )

            product_ids = sorted(
                set(product_urls["ru"])
                | set(product_urls["tr"])
            )

            print()
            print(f"Unique products: {len(product_ids)}")
            print()

            for number, source_id in enumerate(product_ids, start=1):
                print(
                    f"[PRODUCT {number}/{len(product_ids)}] "
                    f"{source_id}"
                )

                old_record = old_record_for(old_products, source_id)
                parsed_sources: dict[str, dict] = {}
                stored_sources = bundle_sources(old_record)

                for language in LANGUAGES:
                    url = product_urls[language].get(source_id)

                    if not url:
                        continue

                    source = await parse_language_source(
                        page=page,
                        entity_type="product",
                        language=language,
                        url=url,
                        expected_source_id=source_id,
                    )

                    if source is None:
                        await polite_delay()
                        continue

                    parsed_sources[language] = source

                    stored_source, changed = await save_source(
                        storage=storage,
                        kind="products",
                        source=source,
                        old_source_hash=old_bundle_source_hash(
                            old_record,
                            language,
                        ),
                        old_source=stored_sources.get(language),
                    )
                    stored_sources[language] = stored_source

                    print(
                        f"  {language}: "
                        f"{'CHANGED' if changed else 'unchanged'}; "
                        f"tabs={len(source.get('tabs', []))}"
                    )
                    await polite_delay()

                if not parsed_sources:
                    if old_record is not None:
                        print("  parse failed; keeping previous site record")
                        product_records[str(source_id)] = old_record
                        product_index.append(
                            make_index_item_from_record(old_record)
                        )
                    continue

                old_data = bundle_data(old_record)

                images = await sync_entity_images(
                    storage=storage,
                    kind="products",
                    source_id=source_id,
                    sources=parsed_sources,
                    old_data=old_data,
                )

                data, data_changed = await save_entity_data(
                    storage=storage,
                    kind="products",
                    source_id=source_id,
                    sources=parsed_sources,
                    images=images,
                    old_data=old_data,
                )

                if data_changed:
                    print("  data.json: CHANGED")
                else:
                    print("  data.json: unchanged")

                localizations = bundle_localizations(old_record)
                ru_localization = localization_snapshot(
                    storage=storage,
                    kind="products",
                    source_id=source_id,
                    old_record=old_record,
                    language="ru",
                )

                if isinstance(ru_localization, dict):
                    localizations["ru"] = ru_localization

                record = make_site_record(
                    source_id=source_id,
                    sources=stored_sources,
                    localizations=localizations,
                    data=data,
                )

                if record is None:
                    print("  site record build failed")
                    continue

                product_records[str(source_id)] = record
                product_index.append(
                    make_index_item_from_record(record)
                )

            product_index.sort(key=lambda item: item["source_id"])
            product_index_changed = storage.put_json_if_changed(
                "index/products.json",
                product_index,
                old_data=bundle_index(old_bundle, "products"),
            )
            print(
                "index/products.json: "
                f"{'CHANGED' if product_index_changed else 'unchanged'}"
            )

        finally:
            await browser.close()

    # Important: site.json is now created from the objects we already have in
    # memory after crawling the supplier. No second pass through all R2 entity
    # JSON files happens here.
    bundle, bundle_changed = build_site_bundle_from_memory(
        storage=storage,
        categories=category_records,
        products=product_records,
        old_bundle=old_bundle,
    )

    print()
    print("========== DONE ==========")
    print(f"Categories:  {len(category_index)}")
    print(f"Products:    {len(product_index)}")
    print(f"Site routes: {len(bundle.get('routes', []))}")
    print(
        "Site bundle: "
        f"{'CHANGED' if bundle_changed else 'unchanged'}"
    )
    print("R2 scan:      NO")
    print("Bundle:       index/site.json")


if __name__ == "__main__":
    asyncio.run(main())
