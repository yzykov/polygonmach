import json
import random
import time
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from .config import SETTINGS


_RETRY_DELAYS_SEC = (2, 5, 10, 20, 30)

_RETRYABLE_ERROR_CODES = {
    "InternalError",
    "ServiceUnavailable",
    "SlowDown",
    "RequestTimeout",
    "RequestTimeoutException",
    "Throttling",
    "ThrottlingException",
}


class R2Storage:
    def __init__(self) -> None:
        self.bucket = SETTINGS.r2_bucket
        self.public_url = SETTINGS.r2_public_url

        self.s3 = boto3.client(
            "s3",
            endpoint_url=SETTINGS.r2_endpoint,
            aws_access_key_id=SETTINGS.r2_access_key_id,
            aws_secret_access_key=SETTINGS.r2_secret_access_key,
            region_name="auto",
            config=Config(
                retries={
                    "total_max_attempts": 5,
                    "mode": "adaptive",
                },
                connect_timeout=15,
                read_timeout=60,
                tcp_keepalive=True,
            ),
        )

    @staticmethod
    def _client_error_info(
        exc: ClientError,
    ) -> tuple[str, int | None]:
        error = exc.response.get("Error", {})
        metadata = exc.response.get("ResponseMetadata", {})

        code = str(error.get("Code", ""))
        status = metadata.get("HTTPStatusCode")

        return code, status

    @classmethod
    def _is_retryable_client_error(
        cls,
        exc: ClientError,
    ) -> bool:
        code, status = cls._client_error_info(exc)

        if code in _RETRYABLE_ERROR_CODES:
            return True

        return isinstance(status, int) and status >= 500

    def _request_with_retry(
        self,
        operation: str,
        **kwargs: Any,
    ) -> Any:
        request = getattr(self.s3, operation)

        for attempt in range(len(_RETRY_DELAYS_SEC) + 1):
            try:
                return request(**kwargs)

            except ClientError as exc:
                if (
                    not self._is_retryable_client_error(exc)
                    or attempt >= len(_RETRY_DELAYS_SEC)
                ):
                    raise

                code, status = self._client_error_info(exc)
                delay = (
                    _RETRY_DELAYS_SEC[attempt]
                    + random.uniform(0.0, 1.0)
                )

                print(
                    f"R2 temporary error "
                    f"{code or status or 'unknown'}, "
                    f"retry {attempt + 1}/"
                    f"{len(_RETRY_DELAYS_SEC)} "
                    f"in {delay:.1f}s"
                )

                time.sleep(delay)

            except BotoCoreError as exc:
                if attempt >= len(_RETRY_DELAYS_SEC):
                    raise

                delay = (
                    _RETRY_DELAYS_SEC[attempt]
                    + random.uniform(0.0, 1.0)
                )

                print(
                    f"R2 network error "
                    f"{type(exc).__name__}, "
                    f"retry {attempt + 1}/"
                    f"{len(_RETRY_DELAYS_SEC)} "
                    f"in {delay:.1f}s"
                )

                time.sleep(delay)

        raise RuntimeError(
            f"Unexpected retry state for R2 operation: {operation}"
        )

    def get_json(
        self,
        key: str,
    ) -> dict | list | None:
        try:
            response = self._request_with_retry(
                "get_object",
                Bucket=self.bucket,
                Key=key,
            )
        except ClientError as exc:
            code, status = self._client_error_info(exc)

            if (
                code in {"404", "NoSuchKey", "NotFound"}
                or status == 404
            ):
                return None

            raise

        return json.loads(
            response["Body"].read().decode("utf-8")
        )

    def put_json(
        self,
        key: str,
        data: dict | list,
    ) -> None:
        body = json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ).encode("utf-8")

        print(
            f"R2 PUT JSON: key={key}, "
            f"size={len(body)} bytes"
        )

        self._request_with_retry(
            "put_object",
            Bucket=self.bucket,
            Key=key,
            Body=body,
            ContentType="application/json; charset=utf-8",
        )

    def put_json_if_changed(
        self,
        key: str,
        data: dict | list,
        old_data: dict | list | None = None,
    ) -> bool:
        if old_data is None:
            old_data = self.get_json(key)

        if old_data == data:
            return False

        self.put_json(key, data)
        return True

    def put_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        self._request_with_retry(
            "put_object",
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
            Metadata=metadata or {},
        )

    def delete(
        self,
        key: str,
    ) -> None:
        self._request_with_retry(
            "delete_object",
            Bucket=self.bucket,
            Key=key,
        )

    def public_object_url(
        self,
        key: str,
    ) -> str | None:
        if not self.public_url:
            return None

        return f"{self.public_url}/{key}"
