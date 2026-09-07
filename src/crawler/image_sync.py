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
) -> dict | None:
    headers = {
        "User-Agent": USER_AGENT,
        "Connection": "close",
    }

    if old_image:
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

        if old_image:
            print("    Keeping existing R2 image")
            return old_image

    new_etag = None
    new_last_modified = None

    if head is not None:
        if head.status_code == 304 and old_image:
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

                if old_image:
                    return old_image

                return None

            new_etag = head.headers.get("ETag")
            new_last_modified = head.headers.get(
                "Last-Modified"
            )

            if old_image:
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

        if old_image:
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

        if old_image:
            return old_image

        return None

    data = response.content
    sha256 = hashlib.sha256(data).hexdigest()

    r2_key = (
        old_image.get("r2_key")
        if old_image and old_image.get("r2_key")
        else make_image_key(
            kind,
            source_id,
            source_url,
        )
    )

    content_type = (
        response.headers
        .get("Content-Type", "")
        .split(";", 1)[0]
        .strip()
    )

    if not content_type:
        content_type = (
            mimetypes.guess_type(source_url)[0]
            or "application/octet-stream"
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
        old_image
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
            )

            if image is not None:
                result.append(image)

            await asyncio.sleep(
                random.uniform(0.3, 0.8)
            )

    return result