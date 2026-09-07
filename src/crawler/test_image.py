import asyncio

from .image_sync import sync_images
from .r2_storage import R2Storage


SOURCE_URL = (
    "https://polygonmach.com/assets/images/editor/"
    "polygonmachcom_5312.webp"
)

STATE_KEY = "test/image.json"


async def main() -> None:
    storage = R2Storage()

    old_state = storage.get_json(STATE_KEY)
    old_images = (
        old_state.get("images", [])
        if isinstance(old_state, dict)
        else []
    )

    images = await sync_images(
        storage=storage,
        kind="test",
        source_id=1,
        source_urls=[SOURCE_URL],
        old_images=old_images,
    )

    state = {
        "source_url": SOURCE_URL,
        "images": images,
    }

    if storage.put_json_if_changed(
        STATE_KEY,
        state,
        old_state,
    ):
        print("TEST JSON uploaded")
    else:
        print("TEST JSON unchanged")

    image = images[0]

    print()
    print(f"r2_key: {image.get('r2_key')}")
    print(f"etag: {image.get('etag')}")
    print(f"sha256: {image.get('sha256')}")
    print(f"url: {image.get('url', '-')}")


if __name__ == "__main__":
    asyncio.run(main())
