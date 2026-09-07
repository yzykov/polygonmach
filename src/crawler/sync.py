import asyncio
from datetime import datetime, timezone

from playwright.async_api import async_playwright

from .browser import open_page, polite_delay
from .config import SETTINGS
from .content_resolver import get_content
from .image_sync import sync_images
from .parser import discover_categories, extract_source
from .r2_storage import R2Storage


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


async def save_source(
    storage: R2Storage,
    kind: str,
    source: dict,
) -> tuple[dict, bool]:
    source_id = source["source_id"]
    language = source["language"]
    key = source_key(kind, source_id, language)

    old = storage.get_json(key)

    clean_source = {
        key_: value
        for key_, value in source.items()
        if not key_.startswith("_") and key_ != "source_images"
    }

    if (
        isinstance(old, dict)
        and old.get("source_hash") == clean_source["source_hash"]
    ):
        return old, False

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
        if image.get("source_url")
    }

    old_source_urls = list(old_by_source)

    # Полностью совпадает — вообще ничего не делаем.
    if source_urls == old_source_urls:
        print("  images: skipped (same source URLs)")
        return old_images

    # Все необходимые картинки уже есть в R2.
    # Например миграция со старой RU+TR схемы 12 -> RU-only 6.
    if all(url in old_by_source for url in source_urls):
        print(
            f"  images: reused existing "
            f"({len(old_images)} -> {len(source_urls)})"
        )

        return [
            old_by_source[url]
            for url in source_urls
        ]

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
) -> dict:
    key = data_key(kind, source_id)
    old = storage.get_json(key)

    source_meta = {}

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

    if isinstance(old, dict):
        comparable_old = {
            "source_id": old.get("source_id"),
            "sources": old.get("sources", {}),
            "images": old.get("images", []),
        }

        if comparable_old == data:
            return old

    data["updated_at"] = utc_now()
    storage.put_json(key, data)

    return data


def make_index_item(
    storage: R2Storage,
    kind: str,
    source_id: int,
    data: dict,
) -> dict:
    content = get_content(
        storage,
        kind,
        source_id,
        "ru",
    ) or {}

    images = data.get("images", [])
    main_image = None

    if images:
        main_image = (
            images[0].get("url")
            or images[0].get("r2_key")
        )

    return {
        "source_id": source_id,
        "title": content.get("title", ""),
        "main_image": main_image,
    }


async def main() -> None:
    storage = R2Storage()

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=SETTINGS.headless,
        )

        context = await browser.new_context(
            locale="ru-RU",
            viewport={"width": 1920, "height": 1080},
        )

        page = await context.new_page()

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

        category_index: list[dict] = []

        for number, source_id in enumerate(category_ids, start=1):
            print(
                f"[CATEGORY {number}/{len(category_ids)}] "
                f"{source_id}"
            )

            sources: dict[str, dict] = {}

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

                sources[language] = source

                product_urls[language].update(
                    source.get("_product_urls", {})
                )

                _, changed = await save_source(
                    storage,
                    "categories",
                    source,
                )

                print(
                    f"  {language}: "
                    f"{'CHANGED' if changed else 'unchanged'}"
                )

                await polite_delay()

            if not sources:
                continue

            old_data = storage.get_json(
                data_key("categories", source_id)
            )

            images = await sync_entity_images(
                storage=storage,
                kind="categories",
                source_id=source_id,
                sources=sources,
                old_data=old_data if isinstance(old_data, dict) else None,
            )

            data = await save_entity_data(
                storage=storage,
                kind="categories",
                source_id=source_id,
                sources=sources,
                images=images,
            )

            category_index.append(
                make_index_item(
                    storage,
                    "categories",
                    source_id,
                    data,
                )
            )

        category_index.sort(key=lambda item: item["source_id"])

        storage.put_json_if_changed(
            "index/categories.json",
            category_index,
        )

        product_ids = sorted(
            set(product_urls["ru"])
            | set(product_urls["tr"])
        )

        print()
        print(f"Unique products: {len(product_ids)}")
        print()

        product_index: list[dict] = []

        for number, source_id in enumerate(product_ids, start=1):
            print(
                f"[PRODUCT {number}/{len(product_ids)}] "
                f"{source_id}"
            )

            sources: dict[str, dict] = {}

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

                sources[language] = source

                _, changed = await save_source(
                    storage,
                    "products",
                    source,
                )

                print(
                    f"  {language}: "
                    f"{'CHANGED' if changed else 'unchanged'}"
                )

                await polite_delay()

            if not sources:
                continue

            old_data = storage.get_json(
                data_key("products", source_id)
            )

            images = await sync_entity_images(
                storage=storage,
                kind="products",
                source_id=source_id,
                sources=sources,
                old_data=old_data if isinstance(old_data, dict) else None,
            )

            data = await save_entity_data(
                storage=storage,
                kind="products",
                source_id=source_id,
                sources=sources,
                images=images,
            )

            product_index.append(
                make_index_item(
                    storage,
                    "products",
                    source_id,
                    data,
                )
            )

        product_index.sort(key=lambda item: item["source_id"])

        storage.put_json_if_changed(
            "index/products.json",
            product_index,
        )

        await browser.close()

    print()
    print("========== DONE ==========")
    print(f"Categories: {len(category_index)}")
    print(f"Products:   {len(product_index)}")


if __name__ == "__main__":
    asyncio.run(main())