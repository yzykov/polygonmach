from __future__ import annotations

import argparse
import sys
from pathlib import Path


# This file lives in:
#   <repo>/src/scripts/clear_r2_bucket.py
#
# When executed directly, Python adds only <repo>/src/scripts to sys.path,
# so `import src...` would fail. Add repository root explicitly.
REPO_ROOT = Path(__file__).resolve().parents[2]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from src.crawler.r2_storage import R2Storage  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "List or delete objects from the configured Cloudflare R2 bucket. "
            "Dry-run is the default."
        ),
    )

    parser.add_argument(
        "--prefix",
        default="",
        help=(
            "Delete only objects under this prefix, for example "
            "'products/25/' or 'products/25/images/'. "
            "Empty prefix means the whole bucket."
        ),
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Actually delete objects. "
            "Without this flag nothing is deleted."
        ),
    )

    parser.add_argument(
        "--yes",
        action="store_true",
        help=(
            "Required together with --apply when prefix is empty "
            "(whole-bucket deletion)."
        ),
    )

    return parser.parse_args()


def list_keys(
    storage: R2Storage,
    prefix: str,
):
    paginator = storage.s3.get_paginator(
        "list_objects_v2"
    )

    for page in paginator.paginate(
        Bucket=storage.bucket,
        Prefix=prefix,
    ):
        for item in page.get("Contents", []):
            key = item.get("Key")

            if key:
                yield key


def delete_batch(
    storage: R2Storage,
    keys: list[str],
) -> None:
    if not keys:
        return

    response = storage._request_with_retry(
        "delete_objects",
        Bucket=storage.bucket,
        Delete={
            "Objects": [
                {"Key": key}
                for key in keys
            ],
            "Quiet": False,
        },
    )

    errors = response.get("Errors", [])

    if not errors:
        return

    for error in errors:
        print(
            "DELETE ERROR:",
            error.get("Key"),
            error.get("Code"),
            error.get("Message"),
            file=sys.stderr,
        )

    raise RuntimeError(
        f"R2 returned {len(errors)} delete error(s)"
    )


def main() -> None:
    args = parse_args()

    prefix = (
        args.prefix
        .strip()
        .lstrip("/")
    )

    if (
        args.apply
        and not prefix
        and not args.yes
    ):
        raise SystemExit(
            "Refusing to delete the whole bucket "
            "without --yes. "
            "Use: --apply --yes"
        )

    storage = R2Storage()

    print(
        f"Bucket: {storage.bucket}"
    )
    print(
        f"Prefix: {prefix or '<whole bucket>'}"
    )

    keys = list(
        list_keys(
            storage,
            prefix,
        )
    )

    print(
        f"Objects: {len(keys)}"
    )

    if not keys:
        print("Nothing to do.")
        return

    for key in keys:
        print(
            f"{'DELETE' if args.apply else 'WOULD DELETE'} "
            f"{key}"
        )

    if not args.apply:
        print()
        print(
            "DRY RUN: nothing was deleted."
        )
        print(
            "Add --apply to delete this prefix."
        )

        if not prefix:
            print(
                "For the whole bucket use: "
                "--apply --yes"
            )

        return

    deleted = 0

    for offset in range(
        0,
        len(keys),
        1000,
    ):
        batch = keys[
            offset:offset + 1000
        ]

        delete_batch(
            storage,
            batch,
        )

        deleted += len(batch)

        print(
            f"Deleted "
            f"{deleted}/{len(keys)}"
        )

    print("Done.")


if __name__ == "__main__":
    main()
