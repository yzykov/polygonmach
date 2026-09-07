from .r2_storage import R2Storage


storage = R2Storage()

storage.put_json(
    "categories/18/source/test.json",
    {
        "test": True,
    },
)

print("OK")