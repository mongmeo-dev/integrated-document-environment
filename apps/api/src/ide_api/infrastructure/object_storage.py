from typing import BinaryIO
from uuid import uuid4

import boto3

from ide_api.config import Settings, get_settings


class ObjectStorage:
    def __init__(self, settings: Settings | None = None) -> None:
        storage_settings = settings or get_settings()
        self._bucket = storage_settings.object_storage_bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=storage_settings.object_storage_endpoint_url,
            region_name=storage_settings.object_storage_region,
            aws_access_key_id=storage_settings.object_storage_access_key,
            aws_secret_access_key=storage_settings.object_storage_secret_key,
        )

    def upload(self, content: BinaryIO) -> str:
        object_key = f"documents/{uuid4()}"
        self._client.put_object(
            Bucket=self._bucket,
            Key=object_key,
            Body=content,
            IfNoneMatch="*",
        )
        return object_key

    def download(self, object_key: str) -> BinaryIO:
        response = self._client.get_object(Bucket=self._bucket, Key=object_key)
        return response["Body"]

    def delete(self, object_key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=object_key)
