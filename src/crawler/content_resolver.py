from .r2_storage import R2Storage


def content_key(
    kind: str,
    source_id: int,
    language: str = "ru",
) -> str:
    return f"{kind}/{source_id}/source/{language}.json"


def localization_key(
    kind: str,
    source_id: int,
    language: str = "ru",
) -> str:
    return f"{kind}/{source_id}/localization/{language}.json"


def get_content(
    storage: R2Storage,
    kind: str,
    source_id: int,
    language: str = "ru",
) -> dict | None:
    """
    Site-side resolution rule:

    1. localization/<language>.json
    2. source/<language>.json

    The crawler never writes localization files.
    """
    localized = storage.get_json(
        localization_key(
            kind,
            source_id,
            language,
        )
    )

    if isinstance(localized, dict):
        return localized

    source = storage.get_json(
        content_key(
            kind,
            source_id,
            language,
        )
    )

    return source if isinstance(source, dict) else None
