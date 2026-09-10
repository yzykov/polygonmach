import asyncio
import hashlib
import mimetypes
import random
from pathlib import PurePosixPath
from urllib.parse import urlsplit

import httpx

from .config import SETTINGS
from .r2_storage import R2Storage


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/152.0.0.0 Safari/537.36"
)

RETRY_DELAYS = (2, 5, 10)


_IMAGE_SIGNATURES = {
    "image/jpeg": lambda data: len(data) >= 3 and data[:3] == b"\xff\xd8\xff",
    "image/png": lambda data: len(data) >= 8 and data[:8] == b"\x89PNG\r\n\x1a\n",
    "image/gif": lambda data: data.startswith((b"GIF87a", b"GIF89a")),
    "image/webp": lambda data: (
        len(data) >= 12
        and data[:4] == b"RIFF"
        and data[8:12] == b"WEBP"
    ),
    "image/bmp": lambda data: data.startswith(b"BM"),
    "image/tiff": lambda data: data.startswith((b"II*\x00", b"MM\x00*")),
    "image/avif": lambda data: (
        len(data) >= 12
        and data[4:8] == b"ftyp"
        and b"avif" in data[8:32]
    ),
}


def normalized_content_type(value: str | None) -> str:
    return (
        (value or "")
        .split(";", 1)[0]
        .strip()
        .lower()
    )


def looks_like_image(
    data: bytes,
    content_type: str,
) -> bool:
    if not content_type.startswith("image/"):
        return False

    validator = _IMAGE_SIGNATURES.get(content_type)

    # Unknown image/* type: Content-Type is still better than accepting
    # arbitrary HTML/text. Known formats are additionally checked by bytes.
    if validator is None:
        return bool(data)

    return validator(data)


def old_image_metadata_is_valid(
    image: dict | None,
) -> bool:
    if not isinstance(image, dict):
        return False

    if not image.get("r2_key"):
        return False

    content_type = normalized_content_type(
        image.get("content_type")
    )

    return content_type.startswith("image/")


def make_image_key(
    kind: str,
    source_id: int,
    source_url: str,
) -> str:
    extension = PurePosixPath(
        urlsplit(source_url).path
    ).suffix.lower()

    if not extension or len(extension) > 6:
        extension = ".bin"

    url_hash = hashlib.sha1(
        source_url.encode("utf-8")
    ).hexdigest()[:16]

    return f"{kind}/{source_id}/images/{url_hash}{extension}"


async def request_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    headers: dict[str, str],
) -> httpx.Response | None:
    for attempt, delay in enumerate(RETRY_DELAYS, start=1):
        try:
            response = await client.request(
                method,
                url,
                headers=headers,
                follow_redirects=True,
                timeout=SETTINGS.http_timeout_sec,
            )

            if response.status_code == 429:
                print(
                    f"    IMAGE 429, attempt "
                    f"{attempt}/{len(RETRY_DELAYS)}, "
                    f"sleep {delay}s"
                )
                await asyncio.sleep(delay)
                continue

            if response.status_code >= 500:
                print(
                    f"    IMAGE HTTP {response.status_code}, "
                    f"attempt {attempt}/{len(RETRY_DELAYS)}, "
                    f"sleep {delay}s"
                )
                await asyncio.sleep(delay)
                continue

            return response

        except (
            httpx.RemoteProtocolError,
            httpx.ConnectError,
            httpx.ReadError,
            httpx.ReadTimeout,
            httpx.ConnectTimeout,
        ) as exc:
            print(
                f"    IMAGE network error, "
                f"attempt {attempt}/{len(RETRY_DELAYS)}: "
                f"{exc}"
            )

            if attempt < len(RETRY_DELAYS):
                await asyncio.sleep(delay)

    return None


async def sync_image(
    client: httpx.AsyncClient,
    storage: R2Storage,
    kind: str,
    source_id: int,
    source_url: str,
    old_image: dict | None,
    force_refresh: bool = False,
) -> dict | None:
    headers = {
        "User-Agent": USER_AGENT,
        "Connection": "close",
    }

    has_r2_copy = (
        not force_refresh
        and old_image_metadata_is_valid(old_image)
    )

    # Conditional requests are safe only when we really have a stored R2
    # object to reuse. Old metadata without r2_key must be repaired by GET.
    if has_r2_copy:
        if old_image.get("etag"):
            headers["If-None-Match"] = old_image["etag"]

        if old_image.get("last_modified"):
            headers["If-Modified-Since"] = old_image["last_modified"]

    head = await request_with_retry(
        client,
        "HEAD",
        source_url,
        headers,
    )

    if head is None:
        print(f"    IMAGE HEAD failed: {source_url}")

        if has_r2_copy:
            print("    Keeping existing R2 image")
            return old_image

    new_etag = None
    new_last_modified = None

    if head is not None:
        if head.status_code == 304 and has_r2_copy:
            print(f"    IMAGE unchanged: {source_url}")
            return old_image

        if head.status_code not in {405, 501}:
            try:
                head.raise_for_status()
            except httpx.HTTPStatusError as exc:
                print(
                    f"    IMAGE HEAD failed "
                    f"HTTP {head.status_code}: {source_url}"
                )

                if has_r2_copy:
                    return old_image

                return None

            new_etag = head.headers.get("ETag")
            new_last_modified = head.headers.get(
                "Last-Modified"
            )

            if has_r2_copy:
                old_etag = old_image.get("etag")
                old_last_modified = old_image.get(
                    "last_modified"
                )

                if (
                    new_etag
                    and old_etag
                    and new_etag == old_etag
                ):
                    print(
                        f"    IMAGE unchanged: "
                        f"{source_url}"
                    )
                    return old_image

                if (
                    not new_etag
                    and new_last_modified
                    and old_last_modified
                    and new_last_modified
                    == old_last_modified
                ):
                    print(
                        f"    IMAGE unchanged: "
                        f"{source_url}"
                    )
                    return old_image

    response = await request_with_retry(
        client,
        "GET",
        source_url,
        {
            "User-Agent": USER_AGENT,
            "Connection": "close",
        },
    )

    if response is None:
        print(f"    IMAGE GET failed: {source_url}")

        if has_r2_copy:
            print("    Keeping existing R2 image")
            return old_image

        return None

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError:
        print(
            f"    IMAGE GET HTTP "
            f"{response.status_code}: {source_url}"
        )

        if has_r2_copy:
            return old_image

        return None

    data = response.content

    content_type = normalized_content_type(
        response.headers.get("Content-Type")
    )

    if not content_type:
        content_type = normalized_content_type(
            mimetypes.guess_type(source_url)[0]
        )

    if not looks_like_image(data, content_type):
        preview = data[:80].replace(
            b"\r",
            b" ",
        ).replace(
            b"\n",
            b" ",
        )

        print(
            f"    IMAGE invalid response: "
            f"content_type={content_type or '<empty>'!r}, "
            f"bytes={preview!r}: {source_url}"
        )

        if has_r2_copy:
            print("    Keeping existing validated R2 image")
            return old_image

        return None

    sha256 = hashlib.sha256(data).hexdigest()

    r2_key = (
        old_image.get("r2_key")
        if has_r2_copy
        else make_image_key(
            kind,
            source_id,
            source_url,
        )
    )

    response_etag = (
        response.headers.get("ETag")
        or new_etag
    )

    response_last_modified = (
        response.headers.get("Last-Modified")
        or new_last_modified
    )

    if (
        has_r2_copy
        and old_image.get("sha256") == sha256
    ):
        print(
            f"    IMAGE bytes unchanged: "
            f"{source_url}"
        )

        return {
            **old_image,
            "etag": response_etag,
            "last_modified": response_last_modified,
            "sha256": sha256,
            "content_type": content_type,
        }

    metadata = {
        "sha256": sha256,
    }

    if response_etag:
        metadata["source-etag"] = (
            response_etag.strip('"')
        )

    storage.put_bytes(
        key=r2_key,
        data=data,
        content_type=content_type,
        metadata=metadata,
    )

    result = {
        "source_url": source_url,
        "r2_key": r2_key,
        "etag": response_etag,
        "last_modified": response_last_modified,
        "sha256": sha256,
        "content_type": content_type,
    }

    public_url = storage.public_object_url(
        r2_key
    )

    if public_url:
        result["url"] = public_url

    print(f"    IMAGE uploaded: {r2_key}")

    return result


async def sync_images(
    storage: R2Storage,
    kind: str,
    source_id: int,
    source_urls: list[str],
    old_images: list[dict] | None = None,
    force_refresh: bool = False,
) -> list[dict]:
    old_by_source = {
        image["source_url"]: image
        for image in (old_images or [])
        if image.get("source_url")
    }

    result: list[dict] = []

    limits = httpx.Limits(
        max_connections=1,
        max_keepalive_connections=0,
    )

    async with httpx.AsyncClient(
        limits=limits,
        http2=False,
    ) as client:
        for source_url in source_urls:
            image = await sync_image(
                client=client,
                storage=storage,
                kind=kind,
                source_id=source_id,
                source_url=source_url,
                old_image=old_by_source.get(
                    source_url
                ),
                force_refresh=force_refresh,
            )

            if image is not None:
                result.append(image)

            await asyncio.sleep(
                random.uniform(0.3, 0.8)
            )

    return result