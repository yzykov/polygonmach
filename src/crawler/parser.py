import hashlib
import json
import re
from urllib.parse import urljoin, urlsplit, urlunsplit

from playwright.async_api import Locator, Page

from .config import SETTINGS


SOURCE_ID_RE = re.compile(r"-(\d+)\.html$")


def clean_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def normalize_media_url(page_url: str, value: str) -> str:
    """
    Polygonmach has image attributes such as:

        assets/images/...

    They are effectively site-root assets, but urljoin(page_url, value)
    would incorrectly produce:

        /ru/product/assets/...
        /ru/category/assets/...

    Normalize every URL containing /assets/ back to the site root.
    """
    url = clean_url(urljoin(page_url, value.strip()))
    parts = urlsplit(url)

    marker = "/assets/"
    position = parts.path.find(marker)

    if position > 0:
        return urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                parts.path[position:],
                "",
                "",
            )
        )

    return url


def get_source_id(url: str) -> int | None:
    match = SOURCE_ID_RE.search(urlsplit(url).path)
    return int(match.group(1)) if match else None


def make_hash(data: dict) -> str:
    raw = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def collect_links(
    scope: Locator,
    pattern: str,
) -> dict[int, str]:
    hrefs = await scope.locator(
        f'a[href*="{pattern}"]'
    ).evaluate_all(
        "elements => elements.map(element => element.href)"
    )

    result: dict[int, str] = {}

    for href in hrefs:
        url = clean_url(href)
        source_id = get_source_id(url)
        if source_id is not None:
            result[source_id] = url

    return result


async def discover_categories(
    page: Page,
    language: str,
) -> dict[int, str]:
    return await collect_links(
        page.locator("body"),
        f"/{language}/category/",
    )


async def collect_card_links(
    scope: Locator,
    pattern: str,
) -> dict[int, str]:
    """
    Collect links that belong to visual content cards.

    The Polygonmach main container also contains large navigation/menu blocks.
    A plain search for every /category/ or /product/ link therefore flattens
    the whole catalog.

    Real category/product tiles are associated with an image. We keep a link
    only when the link itself or one of its close ancestors contains an image
    and only a small number of catalog links.
    """
    hrefs = await scope.locator(
        f'a[href*="{pattern}"]'
    ).evaluate_all(
        r"""
        links => links
            .filter(link => {
                let node = link;

                for (let depth = 0; depth < 5 && node; depth += 1) {
                    const hasImage = Boolean(node.querySelector('img'));
                    const catalogLinks = node.querySelectorAll(
                        'a[href*="/category/"], a[href*="/product/"]'
                    ).length;

                    if (hasImage && catalogLinks <= 4) {
                        return true;
                    }

                    node = node.parentElement;
                }

                return false;
            })
            .map(link => link.href)
        """
    )

    result: dict[int, str] = {}

    for href in hrefs:
        url = clean_url(href)
        source_id = get_source_id(url)

        if source_id is not None:
            result[source_id] = url

    return result


async def discover_child_categories(
    container: Locator,
    language: str,
) -> dict[int, str]:
    return await collect_card_links(
        container,
        f"/{language}/category/",
    )


async def discover_products(
    container: Locator,
    language: str,
) -> dict[int, str]:
    return await collect_card_links(
        container,
        f"/{language}/product/",
    )


async def get_canonical_url(page: Page) -> str:
    locator = page.locator('link[rel="canonical"]').first

    if await locator.count():
        value = await locator.get_attribute("href")
        if value:
            return clean_url(urljoin(page.url, value))

    return clean_url(page.url)


async def get_title(page: Page) -> str:
    h1 = page.locator("h1").first

    if await h1.count():
        title = (await h1.inner_text()).strip()
        if title:
            return title

    return (await page.title()).strip()


async def extract_main_content(container: Locator) -> dict:
    return await container.evaluate(
        r"""
        container => {
            const clean = value =>
                (value || '').replace(/\s+/g, ' ').trim();

            const rows = [...container.querySelectorAll('.row')];
            let textColumn = null;

            for (const row of rows) {
                const columns = [...row.children].filter(element => {
                    if (typeof element.className !== 'string') {
                        return false;
                    }
                    return /(^|\s)col(?:-|\s|$)/.test(element.className);
                });

                const imageColumn = columns.find(
                    column => column.querySelector('img')
                );

                const candidate = columns.find(
                    column =>
                        column !== imageColumn &&
                        clean(column.innerText).length > 30
                );

                if (candidate) {
                    textColumn = candidate;
                    break;
                }
            }

            if (!textColumn) {
                textColumn = container;
            }

            return {
                text: clean(textColumn.innerText),
                html: textColumn.innerHTML.trim(),
            };
        }
        """
    )


async def extract_image_urls(
    container: Locator,
    page_url: str,
) -> list[str]:
    candidates = await container.locator("img").evaluate_all(
        r"""
        images => images.map(img => {
            const link = img.closest('a[href]');

            return {
                link:
                    link
                        ? (link.getAttribute('href') || '')
                        : '',
                original:
                    img.dataset.original ||
                    img.dataset.full ||
                    '',
                preview:
                    img.dataset.src ||
                    img.dataset.lazySrc ||
                    img.getAttribute('src') ||
                    img.currentSrc ||
                    img.src ||
                    ''
            };
        })
        """
    )

    result: list[str] = []
    seen: set[str] = set()
    source_host = urlsplit(SETTINGS.source_base_url).netloc

    for image in candidates:
        selected = ""

        for candidate in (
            image.get("link", ""),
            image.get("original", ""),
            image.get("preview", ""),
        ):
            if candidate and re.search(
                r"\.(jpg|jpeg|png|webp|avif)(\?.*)?$",
                candidate,
                re.IGNORECASE,
            ):
                selected = candidate
                break

        if not selected:
            continue

        url = normalize_media_url(page_url, selected)

        if urlsplit(url).netloc != source_host:
            continue

        lower = url.lower()

        if any(
            marker in lower
            for marker in ("logo", "favicon", "/icon", "flag", "language")
        ):
            continue

        if url in seen:
            continue

        seen.add(url)
        result.append(url)

    return result


def parse_specifications(text: str) -> dict[str, str]:
    result: dict[str, str] = {}

    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()

        if not line or len(line) > 250:
            continue

        if ":" in line:
            key, value = line.split(":", 1)
        elif " - " in line:
            key, value = line.split(" - ", 1)
        else:
            continue

        key = key.strip()
        value = value.strip()

        if (
            not key
            or not value
            or len(key) > 100
            or len(value) > 180
        ):
            continue

        result[key] = value

    return result


async def extract_source(
    page: Page,
    entity_type: str,
    language: str,
) -> dict | None:
    container = page.locator("div.main > div.container").first

    if not await container.count():
        print("  div.main > div.container not found")
        return None

    source_url = await get_canonical_url(page)
    source_id = get_source_id(source_url)

    if source_id is None:
        print("  source_id not found")
        return None

    title = await get_title(page)
    content = await extract_main_content(container)
    image_urls = await extract_image_urls(container, source_url)

    category_urls: dict[int, str] = {}
    product_urls: dict[int, str] = {}

    if entity_type == "category":
        category_urls = await discover_child_categories(
            container,
            language,
        )
        category_urls.pop(source_id, None)

        product_urls = await discover_products(
            container,
            language,
        )

    hash_data = {
        "title": title,
        "text": content["text"],
        "html": content["html"],
        "image_urls": image_urls,
        "category_ids": sorted(category_urls),
        "product_ids": sorted(product_urls),
    }

    result = {
        "language": language,
        "source_id": source_id,
        "source_url": source_url,
        "source_hash": make_hash(hash_data),
        "title": title,
        "text": content["text"],
        "html": content["html"],
        "source_images": image_urls,
    }

    if entity_type == "category":
        result["category_ids"] = sorted(category_urls)
        result["product_ids"] = sorted(product_urls)
        result["_category_urls"] = category_urls
        result["_product_urls"] = product_urls
    else:
        result["specifications"] = parse_specifications(content["text"])

    return result
