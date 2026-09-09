from .r2_storage import R2Storage
from .site_bundle import build_site_bundle


def main() -> None:
    print(
        "RECOVERY MODE: this command rebuilds index/site.json by reading "
        "all existing entity JSON files from R2 sequentially."
    )
    print(
        "Do not use it as the regular weekly crawler job. "
        "For normal supplier sync use: python -m src.crawler.sync"
    )
    print()

    storage = R2Storage()
    bundle = build_site_bundle(storage)

    print()
    print("========== SITE BUNDLE RECOVERY DONE ==========")
    print(f"Categories: {len(bundle.get('categories', {}))}")
    print(f"Products:   {len(bundle.get('products', {}))}")
    print(f"Routes:     {len(bundle.get('routes', []))}")
    print("R2 object:  index/site.json")


if __name__ == "__main__":
    main()
