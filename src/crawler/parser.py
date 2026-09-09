import hashlib
import json
import re
from html import escape
from urllib.parse import urljoin, urlsplit, urlunsplit

from playwright.async_api import Locator, Page

from .config import SETTINGS


SOURCE_ID_RE = re.compile(r"-(\d+)\.html$")
IMAGE_SRC_RE = re.compile(
    r'(<img\b[^>]*?\bsrc\s*=\s*)(["\'])(.*?)(\2)',
    re.IGNORECASE | re.DOTALL,
)


def clean_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def normalize_media_url(page_url: str, value: str) -> str:
    value = value.strip()

    if not value:
        return ""

    url = clean_url(urljoin(page_url, value))
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


def normalize_html_image_urls(html: str, page_url: str) -> str:
    def replace(match: re.Match[str]) -> str:
        prefix = match.group(1)
        quote = match.group(2)
        value = match.group(3)
        normalized = normalize_media_url(page_url, value)
        return f"{prefix}{quote}{escape(normalized, quote=True)}{quote}"

    return IMAGE_SRC_RE.sub(replace, html)


def extract_image_urls_from_html(html: str, page_url: str) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for match in IMAGE_SRC_RE.finditer(html):
        value = match.group(3).strip()

        if not value:
            continue

        url = normalize_media_url(page_url, value)

        if not url or url in seen:
            continue

        seen.add(url)
        result.append(url)

    return result


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
    Keep links that belong to actual category/product cards instead of
    flattening the large common navigation accordion into every category.
    """
    hrefs = await scope.locator(
        f'a[href*="{pattern}"]'
    ).evaluate_all(
        r"""
        links => links
            .filter(link => {
                if (link.closest('article.code, .palovit-accordion, #accordion')) {
                    return false;
                }

                let node = link;

                for (let depth = 0; depth < 6 && node; depth += 1) {
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
    """
    Category descriptions can span multiple rows. Collect every meaningful
    text column instead of stopping after the first one.
    """
    return await container.evaluate(
        r"""
        container => {
            const clean = value =>
                (value || '').replace(/\s+/g, ' ').trim();

            const isColumn = element => {
                if (typeof element.className !== 'string') {
                    return false;
                }

                return /(^|\s)col(?:-|\s|$)/.test(element.className);
            };

            const isIgnored = element => {
                if (!element) {
                    return true;
                }

                if (
                    element.closest(
                        'article.code, #accordion, .palovit-accordion, ' +
                        'nav, header, footer, .breadcrumb, .breadcrumbs'
                    )
                ) {
                    return true;
                }

                if (
                    element.querySelector(
                        'article.code, #accordion, .palovit-accordion'
                    )
                ) {
                    return true;
                }

                return false;
            };

            const hasUsefulText = element => {
                const text = clean(element.innerText);

                if (text.length <= 30) {
                    return false;
                }

                const links = [...element.querySelectorAll('a')];
                const linkText = links
                    .map(link => clean(link.innerText))
                    .join(' ');

                if (
                    links.length >= 3 &&
                    linkText.length > text.length * 0.72
                ) {
                    return false;
                }

                return true;
            };

            const candidates = [];

            for (const row of container.querySelectorAll('.row')) {
                const columns = [...row.children].filter(isColumn);

                for (const column of columns) {
                    if (isIgnored(column)) {
                        continue;
                    }

                    if (!hasUsefulText(column)) {
                        continue;
                    }

                    // A product/category card contains an image and catalog link.
                    // Long-form article columns may contain images too, so only
                    // reject image columns when they also look like navigation.
                    const catalogLinks = column.querySelectorAll(
                        'a[href*="/category/"], a[href*="/product/"]'
                    ).length;

                    if (column.querySelector('img') && catalogLinks > 0) {
                        continue;
                    }

                    candidates.push(column);
                }
            }

            const unique = candidates.filter(
                (candidate, index) =>
                    !candidates.some(
                        (other, otherIndex) =>
                            otherIndex !== index &&
                            other.contains(candidate)
                    )
            );

            if (!unique.length) {
                const clone = container.cloneNode(true);

                clone.querySelectorAll(
                    'script, style, noscript, form, nav, header, footer, ' +
                    'article.code, #accordion, .palovit-accordion, ' +
                    '.breadcrumb, .breadcrumbs'
                ).forEach(element => element.remove());

                return {
                    text: clean(clone.innerText),
                    html: clone.innerHTML.trim(),
                };
            }

            return {
                text: unique
                    .map(element => clean(element.innerText))
                    .filter(Boolean)
                    .join('\n\n'),
                html: unique
                    .map(element => element.innerHTML.trim())
                    .filter(Boolean)
                    .join('\n'),
            };
        }
        """
    )


async def extract_product_tabs(
    container: Locator,
    page_url: str,
) -> list[dict]:
    raw_tabs = await container.evaluate(
        r"""
        container => {
            const clean = value =>
                (value || '').replace(/\s+/g, ' ').trim();

            const cleanLines = value =>
                (value || '')
                    .split(/\n+/)
                    .map(line => clean(line))
                    .filter(Boolean)
                    .join('\n');

            const links = [
                ...container.querySelectorAll(
                    'ul.nav-tabs a[href^="#"], ' +
                    '.nav.nav-tabs a[href^="#"], ' +
                    'a[role="tab"][href^="#"]'
                )
            ];

            const result = [];
            const seen = new Set();

            for (const link of links) {
                const href = (link.getAttribute('href') || '').trim();

                if (!href.startsWith('#') || href.length <= 1) {
                    continue;
                }

                const id = href.slice(1);

                if (seen.has(id)) {
                    continue;
                }

                const target = document.getElementById(id);

                if (!target || !container.contains(target)) {
                    continue;
                }

                const title = clean(link.innerText || link.textContent);

                if (!title) {
                    continue;
                }

                seen.add(id);
                result.push({
                    id,
                    title,
                    text: cleanLines(target.innerText),
                    html: target.innerHTML.trim(),
                });
            }

            return result;
        }
        """
    )

    result: list[dict] = []

    for tab in raw_tabs:
        result.append(
            {
                "id": tab.get("id", ""),
                "title": tab.get("title", ""),
                "text": tab.get("text", ""),
                "html": normalize_html_image_urls(
                    tab.get("html", ""),
                    page_url,
                ),
            }
        )

    return result


def is_auxiliary_product_tab(tab: dict) -> bool:
    title = str(tab.get("title", "")).casefold()

    return any(
        marker in title
        for marker in (
            "галере",
            "gallery",
            "galeri",
            "получить цену",
            "get price",
            "fiyat",
        )
    )


def primary_product_content(tabs: list[dict]) -> dict | None:
    for tab in tabs:
        if is_auxiliary_product_tab(tab):
            continue

        text = str(tab.get("text", "")).strip()
        html = str(tab.get("html", "")).strip()

        if text or html:
            return {
                "text": text,
                "html": html,
            }

    return None


async def extract_breadcrumbs(
    page: Page,
    language: str,
) -> list[dict]:
    items = await page.locator(
        ".breadcrumb a, .breadcrumbs a, ol.breadcrumb a"
    ).evaluate_all(
        r"""
        elements => elements.map(element => ({
            href: element.href || '',
            title: (element.innerText || '')
                .replace(/\s+/g, ' ')
                .trim()
        }))
        """
    )

    result: list[dict] = []
    seen: set[int] = set()

    for item in items:
        href = clean_url(item.get("href", ""))
        title = item.get("title", "").strip()

        if f"/{language}/category/" not in href:
            continue

        source_id = get_source_id(href)

        if (
            source_id is None
            or source_id in seen
            or not title
        ):
            continue

        seen.add(source_id)
        result.append(
            {
                "source_id": source_id,
                "title": title,
            }
        )

    return result


async def extract_image_urls(
    container: Locator,
    page_url: str,
) -> list[str]:
    candidates = await container.locator("img").evaluate_all(
        r"""
        images => images
            .filter(img => !img.closest(
                'article.code, .palovit-accordion, #accordion'
            ))
            .map(img => {
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
            for marker in (
                "logo",
                "favicon",
                "/icon",
                "flag",
                "language",
            )
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
    breadcrumbs = await extract_breadcrumbs(page, language)

    category_urls: dict[int, str] = {}
    product_urls: dict[int, str] = {}
    tabs: list[dict] = []

    if entity_type == "product":
        tabs = await extract_product_tabs(container, source_url)
        primary = primary_product_content(tabs)

        if primary is not None:
            content = primary
        else:
            print(
                "  product tabs not found, "
                "using fallback content extractor"
            )
            content = await extract_main_content(container)
    else:
        content = await extract_main_content(container)

        category_urls = await discover_child_categories(
            container,
            language,
        )
        category_urls.pop(source_id, None)

        product_urls = await discover_products(
            container,
            language,
        )

    image_urls = await extract_image_urls(container, source_url)

    for tab in tabs:
        for url in extract_image_urls_from_html(
            tab.get("html", ""),
            source_url,
        ):
            if url not in image_urls:
                image_urls.append(url)

    hash_data = {
        "title": title,
        "text": content["text"],
        "html": content["html"],
        "breadcrumbs": breadcrumbs,
        "tabs": tabs,
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
        "breadcrumbs": breadcrumbs,
        "source_images": image_urls,
    }

    if entity_type == "category":
        result["category_ids"] = sorted(category_urls)
        result["product_ids"] = sorted(product_urls)
        result["_category_urls"] = category_urls
        result["_product_urls"] = product_urls
    else:
        result["tabs"] = tabs
        specification_text = "\n".join(
            str(tab.get("text", ""))
            for tab in tabs
            if not is_auxiliary_product_tab(tab)
        )
        result["specifications"] = parse_specifications(
            specification_text or content["text"]
        )

    return result
