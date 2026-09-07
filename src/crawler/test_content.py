from .content_resolver import get_content
from .r2_storage import R2Storage


def main() -> None:
    storage = R2Storage()

    # Change these values after you have synced at least one product.
    source_id = 13

    content = get_content(
        storage=storage,
        kind="products",
        source_id=source_id,
        language="ru",
    )

    if content is None:
        print("Content not found")
        return

    print(f"Title: {content.get('title', '')}")
    print()
    print(content.get("text", ""))


if __name__ == "__main__":
    main()
