import re
from datetime import datetime, timezone
from urllib.parse import unquote, urlsplit

from .content_resolver import localization_key
from .r2_storage import R2Storage


SITE_BUNDLE_KEY = "index/site.json"
SITE_BUNDLE_VERSION = 2


_CYRILLIC = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
    "е": "e", "ё": "e", "ж": "zh", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n",
    "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
    "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "",
    "э": "e", "ю": "yu", "я": "ya",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def source_key(kind: str, source_id: int, language: str = "ru") -> str:
    return f"{kind}/{source_id}/source/{language}.json"


def data_key(kind: str, source_id: int) -> str:
    return f"{kind}/{source_id}/data.json"


def _transliterate(value: str) -> str:
    return "".join(_CYRILLIC.get(char, char) for char in value.casefold())


def _slugify(value: str) -> str:
    value = _transliterate(value)
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-{2,}", "-", value).strip("-")


def slug_from_source_url(
    source_url: str | None,
    title: str,
    source_id: int,
) -> str:
    if source_url:
        file_name = urlsplit(source_url).path.rstrip("/").split("/")[-1]
        source_slug = unquote(file_name)
        source_slug = re.sub(r"\.html?$", "", source_slug, flags=re.IGNORECASE)
        source_slug = source_slug.casefold()
        source_slug = re.sub(r"[^a-z0-9-]+", "-", source_slug)
        source_slug = re.sub(r"-{2,}", "-", source_slug).strip("-")

        if source_slug:
            if source_slug.endswith(f"-{source_id}"):
                return source_slug
            return f"{source_slug}-{source_id}"

    fallback = _slugify(title) or "item"

    if fallback.endswith(f"-{source_id}"):
        return fallback

    return f"{fallback}-{source_id}"


def merge_effective_content(
    source: dict | None,
    localization: dict | None,
) -> dict | None:
    if not isinstance(source, dict):
        return None

    if not isinstance(localization, dict):
        return {
            **source,
            "localized": False,
        }

    result = {
        **source,
        **localization,
        "localized": True,
    }

    source_specs = source.get("specifications")
    localized_specs = localization.get("specifications")

    if isinstance(source_specs, dict) or isinstance(localized_specs, dict):
        result["specifications"] = {
            **(source_specs if isinstance(source_specs, dict) else {}),
            **(
                localized_specs
                if isinstance(localized_specs, dict)
                else {}
            ),
        }

    return result


def _main_image(data: dict | None) -> str | None:
    if not isinstance(data, dict):
        return None

    images = data.get("images")

    if not isinstance(images, list) or not images:
        return None

    first = images[0]

    if not isinstance(first, dict):
        return None

    return (
        first.get("r2_key")
        or first.get("url")
        or first.get("source_url")
    )


def _record(
    source_id: int,
    sources: dict[str, dict],
    localizations: dict[str, dict],
    data: dict | None,
) -> dict | None:
    source = sources.get("ru") or sources.get("tr")

    if not isinstance(source, dict):
        return None

    localization = (
        localizations.get("ru")
        if source is sources.get("ru")
        else None
    )

    content = merge_effective_content(
        source,
        localization if isinstance(localization, dict) else None,
    )

    if content is None:
        return None

    title = str(content.get("title", "")).strip()

    return {
        "index": {
            "source_id": source_id,
            "title": title,
            "main_image": _main_image(data),
        },
        # Raw crawler snapshots are kept in the bundle so the next full sync
        # can compare hashes without reading every source/*.json from R2.
        "sources": {
            language: value
            for language, value in sources.items()
            if isinstance(value, dict)
        },
        # The crawler never writes localization files. This is only a cached
        # snapshot used to build effective RU content without scanning R2.
        "localizations": {
            language: value
            for language, value in localizations.items()
            if isinstance(value, dict)
        },
        "content": content,
        "data": data if isinstance(data, dict) else {
            "source_id": source_id,
            "sources": {},
            "images": [],
        },
    }

def _entity_map(bundle: dict, kind: str) -> dict[str, dict]:
    value = bundle.get(kind)
    return value if isinstance(value, dict) else {}


def _normalize_ids(value: object) -> list[int]:
    if not isinstance(value, list):
        return []

    result: list[int] = []

    for item in value:
        try:
            source_id = int(item)
        except (TypeError, ValueError):
            continue

        if source_id not in result:
            result.append(source_id)

    return result


def _valid_breadcrumb_ids(content: dict, current_id: int) -> list[int]:
    raw = content.get("breadcrumbs")

    if not isinstance(raw, list):
        return []

    result: list[int] = []

    for item in raw:
        if not isinstance(item, dict):
            continue

        try:
            source_id = int(item.get("source_id"))
        except (TypeError, ValueError):
            continue

        if source_id in {1, current_id} or source_id in result:
            continue

        result.append(source_id)

    return result


def _category_parent_map(categories: dict[str, dict]) -> dict[int, int]:
    result: dict[int, int] = {}

    for parent_key, record in categories.items():
        try:
            parent_id = int(parent_key)
        except ValueError:
            continue

        content = record.get("content")

        if not isinstance(content, dict):
            continue

        for child_id in _normalize_ids(content.get("category_ids")):
            if child_id != parent_id and child_id not in result:
                result[child_id] = parent_id

    return result


def _category_depth(category_id: int, parents: dict[int, int]) -> int:
    seen: set[int] = set()
    current: int | None = category_id
    depth = 0

    while current is not None and current != 1 and current not in seen:
        seen.add(current)
        depth += 1
        current = parents.get(current)

    return depth


def _product_parent_map(
    categories: dict[str, dict],
    category_parents: dict[int, int],
) -> dict[int, int]:
    candidates: dict[int, list[int]] = {}

    for category_key, record in categories.items():
        try:
            category_id = int(category_key)
        except ValueError:
            continue

        content = record.get("content")

        if not isinstance(content, dict):
            continue

        for product_id in _normalize_ids(content.get("product_ids")):
            candidates.setdefault(product_id, []).append(category_id)

    result: dict[int, int] = {}

    for product_id, values in candidates.items():
        values.sort(
            key=lambda item: _category_depth(item, category_parents),
            reverse=True,
        )

        if values:
            result[product_id] = values[0]

    return result


def _category_chain(
    category_id: int | None,
    parents: dict[int, int],
) -> list[int]:
    if category_id is None:
        return []

    result: list[int] = []
    seen: set[int] = set()
    current: int | None = category_id

    while current is not None and current != 1 and current not in seen:
        seen.add(current)
        result.append(current)
        current = parents.get(current)

    result.reverse()
    return result


def _category_descriptor(
    categories: dict[str, dict],
    source_id: int,
) -> dict | None:
    record = categories.get(str(source_id))

    if not isinstance(record, dict):
        return None

    content = record.get("content")

    if not isinstance(content, dict):
        return None

    title = str(content.get("title", "")).strip()

    if not title:
        return None

    return {
        "source_id": source_id,
        "title": title,
        "slug": slug_from_source_url(
            str(content.get("source_url", "")) or None,
            title,
            source_id,
        ),
    }


def _complete_category_path(
    category_ids: list[int],
    parents: dict[int, int],
) -> list[int]:
    """Expand partial breadcrumb ids to the full category hierarchy.

    Polygonmach pages do not always expose the complete breadcrumb chain.
    For example, a product may contain only category 5 even though category 5
    belongs to root category 2.  Build the missing parent chain from the
    relationships already discovered while crawling categories.
    """
    result: list[int] = []

    for category_id in category_ids:
        for ancestor_id in _category_chain(category_id, parents):
            if ancestor_id not in result:
                result.append(ancestor_id)

    return result


def _category_ancestor_ids(
    source_id: int,
    content: dict,
    parents: dict[int, int],
) -> list[int]:
    explicit = _valid_breadcrumb_ids(content, source_id)

    if explicit:
        complete = _complete_category_path(explicit, parents)
        return [item for item in complete if item != source_id]

    return _category_chain(parents.get(source_id), parents)


def _product_ancestor_ids(
    source_id: int,
    content: dict,
    product_parents: dict[int, int],
    category_parents: dict[int, int],
) -> list[int]:
    explicit = _valid_breadcrumb_ids(content, source_id)

    if explicit:
        return _complete_category_path(explicit, category_parents)

    return _category_chain(
        product_parents.get(source_id),
        category_parents,
    )


def rebuild_routes(bundle: dict) -> None:
    categories = _entity_map(bundle, "categories")
    products = _entity_map(bundle, "products")

    category_parents = _category_parent_map(categories)
    product_parents = _product_parent_map(
        categories,
        category_parents,
    )

    routes: list[dict] = []

    for key, record in categories.items():
        try:
            source_id = int(key)
        except ValueError:
            continue

        if source_id == 1:
            continue

        content = record.get("content")

        if not isinstance(content, dict):
            continue

        current = _category_descriptor(categories, source_id)

        if current is None:
            continue

        breadcrumbs = [
            descriptor
            for ancestor_id in _category_ancestor_ids(
                source_id,
                content,
                category_parents,
            )
            if (
                descriptor := _category_descriptor(
                    categories,
                    ancestor_id,
                )
            ) is not None
        ]

        routes.append(
            {
                "kind": "category",
                "source_id": source_id,
                "title": current["title"],
                "slug": current["slug"],
                "breadcrumbs": breadcrumbs,
                "segments": [
                    *[item["slug"] for item in breadcrumbs],
                    current["slug"],
                ],
            }
        )

    for key, record in products.items():
        try:
            source_id = int(key)
        except ValueError:
            continue

        content = record.get("content")

        if not isinstance(content, dict):
            continue

        title = str(content.get("title", "")).strip()

        if not title:
            continue

        current_slug = slug_from_source_url(
            str(content.get("source_url", "")) or None,
            title,
            source_id,
        )

        breadcrumbs = [
            descriptor
            for ancestor_id in _product_ancestor_ids(
                source_id,
                content,
                product_parents,
                category_parents,
            )
            if (
                descriptor := _category_descriptor(
                    categories,
                    ancestor_id,
                )
            ) is not None
        ]

        routes.append(
            {
                "kind": "product",
                "source_id": source_id,
                "title": title,
                "slug": current_slug,
                "breadcrumbs": breadcrumbs,
                "segments": [
                    *[item["slug"] for item in breadcrumbs],
                    current_slug,
                ],
            }
        )

    routes.sort(
        key=lambda item: (
            len(item["segments"]),
            item["kind"],
            item["source_id"],
        )
    )

    root_record = categories.get("1")
    root_content = (
        root_record.get("content")
        if isinstance(root_record, dict)
        else None
    )

    if isinstance(root_content, dict):
        root_category_ids = _normalize_ids(
            root_content.get("category_ids")
        )
    else:
        root_category_ids = []

    if not root_category_ids:
        root_category_ids = sorted(
            source_id
            for source_id in (
                int(key)
                for key in categories
                if key.isdigit()
            )
            if source_id != 1 and source_id not in category_parents
        )

    bundle["routes"] = routes
    bundle["root_category_ids"] = root_category_ids


def _comparable_bundle(bundle: dict) -> dict:
    result = dict(bundle)
    result.pop("generated_at", None)
    return result


def write_site_bundle(
    storage: R2Storage,
    bundle: dict,
    old_bundle: dict | None,
) -> tuple[dict, bool]:
    bundle = {
        **bundle,
        "version": SITE_BUNDLE_VERSION,
    }

    rebuild_routes(bundle)

    if (
        isinstance(old_bundle, dict)
        and _comparable_bundle(old_bundle) == _comparable_bundle(bundle)
    ):
        print("site bundle: unchanged")
        return old_bundle, False

    written = {
        **bundle,
        "generated_at": utc_now(),
    }

    storage.put_json(SITE_BUNDLE_KEY, written)
    print("site bundle: CHANGED")
    return written, True


def bundle_entity_map(
    bundle: dict | None,
    kind: str,
) -> dict[str, dict]:
    if not isinstance(bundle, dict):
        return {}

    return dict(_entity_map(bundle, kind))


def bundle_index(bundle: dict | None, kind: str) -> list[dict]:
    entities = bundle_entity_map(bundle, kind)
    result: list[dict] = []

    for key, record in entities.items():
        if not isinstance(record, dict):
            continue

        index = record.get("index")

        if not isinstance(index, dict):
            continue

        try:
            source_id = int(index.get("source_id", key))
        except (TypeError, ValueError):
            continue

        result.append(
            {
                "source_id": source_id,
                "title": str(index.get("title", "")),
                "main_image": index.get("main_image"),
            }
        )

    result.sort(key=lambda item: item["source_id"])
    return result


def bundle_source_hash(
    record: dict | None,
    language: str,
) -> str | None:
    if not isinstance(record, dict):
        return None

    sources = record.get("sources")

    if isinstance(sources, dict):
        source = sources.get(language)

        if isinstance(source, dict):
            value = source.get("source_hash")

            if value:
                return str(value)

    # Compatibility with site bundle v1: data.json already stores source
    # hashes for every language even though raw source snapshots were absent.
    data = record.get("data")

    if isinstance(data, dict):
        source_meta = data.get("sources")

        if isinstance(source_meta, dict):
            meta = source_meta.get(language)

            if isinstance(meta, dict) and meta.get("source_hash"):
                return str(meta["source_hash"])

    if language == "ru":
        content = record.get("content")

        if isinstance(content, dict) and content.get("source_hash"):
            return str(content["source_hash"])

    return None


def bundle_sources(record: dict | None) -> dict[str, dict]:
    if not isinstance(record, dict):
        return {}

    value = record.get("sources")

    if not isinstance(value, dict):
        return {}

    return {
        language: dict(source)
        for language, source in value.items()
        if isinstance(source, dict)
    }


def bundle_localizations(record: dict | None) -> dict[str, dict]:
    if not isinstance(record, dict):
        return {}

    value = record.get("localizations")

    if not isinstance(value, dict):
        return {}

    return {
        language: dict(localization)
        for language, localization in value.items()
        if isinstance(localization, dict)
    }


def bundle_data(record: dict | None) -> dict | None:
    if not isinstance(record, dict):
        return None

    value = record.get("data")
    return dict(value) if isinstance(value, dict) else None


def localization_snapshot(
    storage: R2Storage,
    kind: str,
    source_id: int,
    old_record: dict | None,
    language: str = "ru",
) -> dict | None:
    """
    Return the cached manual localization without doing an R2 GET on every
    normal weekly sync.

    For bundle v2 the raw localization snapshot is already inside site.json.
    For an older v1 bundle we only hit R2 when the old effective content says
    that a localization actually existed. This makes the migration cheap and
    preserves manual overrides.
    """
    cached = bundle_localizations(old_record).get(language)

    if isinstance(cached, dict):
        return cached

    if isinstance(old_record, dict) and "localizations" in old_record:
        return None

    content = (
        old_record.get("content")
        if isinstance(old_record, dict)
        else None
    )

    # Normal sync never scans R2 when there is no bundle record.
    # An existing manual localization can be imported explicitly with
    # build_site_bundle.py. For v1 -> v2 migration we probe only records
    # that are already marked as localized.
    should_probe = False

    if isinstance(content, dict):
        should_probe = bool(content.get("localized"))

    if not should_probe:
        return None

    value = storage.get_json(
        localization_key(kind, source_id, language)
    )

    return value if isinstance(value, dict) else None


def make_site_record(
    source_id: int,
    sources: dict[str, dict],
    localizations: dict[str, dict] | None,
    data: dict | None,
) -> dict | None:
    return _record(
        source_id=source_id,
        sources=sources,
        localizations=localizations or {},
        data=data,
    )


def build_site_bundle_from_memory(
    storage: R2Storage,
    categories: dict[str, dict],
    products: dict[str, dict],
    old_bundle: dict | None,
) -> tuple[dict, bool]:
    """
    Normal/full-sync path.

    The caller has just crawled the supplier and already has every current
    entity in memory. No source/data scan of R2 is performed here.
    """
    bundle = {
        "version": SITE_BUNDLE_VERSION,
        "categories": categories,
        "products": products,
        "routes": [],
        "root_category_ids": [],
    }

    return write_site_bundle(
        storage=storage,
        bundle=bundle,
        old_bundle=old_bundle,
    )


def _load_record_from_r2(
    storage: R2Storage,
    kind: str,
    source_id: int,
) -> dict | None:
    """Recovery-only helper. Reads one entity sequentially from R2."""
    sources: dict[str, dict] = {}

    for language in ("ru", "tr"):
        value = storage.get_json(
            source_key(kind, source_id, language)
        )

        if isinstance(value, dict):
            sources[language] = value

    if not sources:
        return None

    localizations: dict[str, dict] = {}
    localization = storage.get_json(
        localization_key(kind, source_id, "ru")
    )

    if isinstance(localization, dict):
        localizations["ru"] = localization

    data = storage.get_json(data_key(kind, source_id))

    return make_site_record(
        source_id=source_id,
        sources=sources,
        localizations=localizations,
        data=data if isinstance(data, dict) else None,
    )


def build_site_bundle(storage: R2Storage) -> dict:
    """
    Recovery/migration command.

    This intentionally reconstructs index/site.json from existing R2 objects
    and therefore reads every source/localization/data object sequentially.
    Do NOT schedule it as the normal weekly job; use sync.py for that.
    """
    category_index = storage.get_json("index/categories.json")
    product_index = storage.get_json("index/products.json")

    category_items = (
        category_index if isinstance(category_index, list) else []
    )
    product_items = (
        product_index if isinstance(product_index, list) else []
    )

    categories: dict[str, dict] = {}
    products: dict[str, dict] = {}

    print()
    print("========== RECOVER SITE BUNDLE FROM R2 ==========")
    print("WARNING: this command scans entity JSON files sequentially.")

    for number, item in enumerate(category_items, start=1):
        if not isinstance(item, dict):
            continue

        try:
            source_id = int(item.get("source_id"))
        except (TypeError, ValueError):
            continue

        print(
            f"[R2 CATEGORY {number}/{len(category_items)}] "
            f"{source_id}"
        )

        record = _load_record_from_r2(
            storage,
            "categories",
            source_id,
        )

        if record is not None:
            categories[str(source_id)] = record

    for number, item in enumerate(product_items, start=1):
        if not isinstance(item, dict):
            continue

        try:
            source_id = int(item.get("source_id"))
        except (TypeError, ValueError):
            continue

        print(
            f"[R2 PRODUCT {number}/{len(product_items)}] "
            f"{source_id}"
        )

        record = _load_record_from_r2(
            storage,
            "products",
            source_id,
        )

        if record is not None:
            products[str(source_id)] = record

    old_bundle = storage.get_json(SITE_BUNDLE_KEY)
    bundle, _ = build_site_bundle_from_memory(
        storage=storage,
        categories=categories,
        products=products,
        old_bundle=old_bundle if isinstance(old_bundle, dict) else None,
    )

    return bundle


def update_site_bundle_entity(
    storage: R2Storage,
    kind: str,
    source_id: int,
    source_overrides: dict[str, dict],
    data_override: dict,
    old_bundle: dict | None = None,
) -> tuple[dict, bool]:
    """
    Targeted sync path.

    Reads index/site.json once, updates one entity in memory, reads only that
    entity's manual RU localization so an out-of-band localization edit is
    picked up, then writes site.json only if it changed.

    It never falls back to a hidden full R2 scan. If the bundle is missing,
    the caller must explicitly run build_site_bundle.py.
    """
    if old_bundle is None:
        loaded = storage.get_json(SITE_BUNDLE_KEY)
        old_bundle = loaded if isinstance(loaded, dict) else None

    if not isinstance(old_bundle, dict):
        raise RuntimeError(
            "index/site.json is missing. Run "
            "`python -m src.crawler.build_site_bundle` once."
        )

    bundle = {
        **old_bundle,
        "categories": bundle_entity_map(old_bundle, "categories"),
        "products": bundle_entity_map(old_bundle, "products"),
    }

    old_record = bundle[kind].get(str(source_id))
    sources = bundle_sources(old_record)
    sources.update(
        {
            language: value
            for language, value in source_overrides.items()
            if isinstance(value, dict)
        }
    )

    localizations = bundle_localizations(old_record)
    current_localization = storage.get_json(
        localization_key(kind, source_id, "ru")
    )

    if isinstance(current_localization, dict):
        localizations["ru"] = current_localization
    else:
        localizations.pop("ru", None)

    record = make_site_record(
        source_id=source_id,
        sources=sources,
        localizations=localizations,
        data=data_override,
    )

    if record is None:
        raise RuntimeError(
            f"Cannot build site record for {kind}/{source_id}"
        )

    bundle[kind][str(source_id)] = record

    return write_site_bundle(
        storage=storage,
        bundle=bundle,
        old_bundle=old_bundle,
    )
