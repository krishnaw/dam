from abc import ABC, abstractmethod
from datetime import timedelta
from io import BytesIO

from minio import Minio

from app.config import settings


class StorageService(ABC):
    @abstractmethod
    def upload(self, key: str, data: bytes, content_type: str, size: int) -> str:
        ...

    @abstractmethod
    def download(self, key: str) -> bytes:
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        ...

    @abstractmethod
    def get_url(self, key: str, expires: int = 3600) -> str:
        ...


class MinIOStorage(StorageService):
    def __init__(self) -> None:
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket = settings.MINIO_BUCKET

    def ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def upload(self, key: str, data: bytes, content_type: str, size: int) -> str:
        self.client.put_object(
            self.bucket,
            key,
            BytesIO(data),
            length=size,
            content_type=content_type,
        )
        return key

    def download(self, key: str) -> bytes:
        response = self.client.get_object(self.bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete(self, key: str) -> None:
        self.client.remove_object(self.bucket, key)

    def get_url(self, key: str, expires: int = 3600) -> str:
        return self.client.presigned_get_object(
            self.bucket, key, expires=timedelta(seconds=expires)
        )
