import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is not set")
    return value


def env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value else default


@dataclass(frozen=True)
class Settings:
    r2_endpoint: str = required("R2_ENDPOINT")
    r2_bucket: str = required("R2_BUCKET")
    r2_access_key_id: str = required("R2_ACCESS_KEY_ID")
    r2_secret_access_key: str = required("R2_SECRET_ACCESS_KEY")
    r2_public_url: str = os.getenv("R2_PUBLIC_URL", "").rstrip("/")

    source_base_url: str = os.getenv(
        "SOURCE_BASE_URL",
        "https://polygonmach.com",
    ).rstrip("/")

    min_delay_sec: float = env_float("MIN_DELAY_SEC", 2.0)
    max_delay_sec: float = env_float("MAX_DELAY_SEC", 5.0)
    http_timeout_sec: float = env_float("HTTP_TIMEOUT_SEC", 30.0)

    headless: bool = os.getenv("HEADLESS", "true").lower() not in {
        "0", "false", "no",
    }


SETTINGS = Settings()
