import os
import importlib

from storage.backends.filesystem import FileSystemStorage
from storage.backends.s3 import S3Storage
from storage.utils import import_string
from storage.conf import settings




class StorageHandler:

    def __init__(self):
        self.default_storage = self._initialize_storage()


    def _initialize_storage(self):
        try:
            StorageClass = import_string(settings.DEFAULT_STORAGE_BACKEND)
        except:
            raise ValueError(f'Could not import storage class from "{settings.DEFAULT_STORAGE_BACKEND}"')

        if issubclass(StorageClass, FileSystemStorage):
            return StorageClass(
                base_path=settings.BASE_PATH,
                file_permissions=settings.FILE_PERMISSIONS,
            )
        elif issubclass(StorageClass, S3Storage):
            if not settings.S3_BUCKET_NAME:
                raise ValueError("S3_BUCKET_NAME must be set in environment variables.")

            return StorageClass(
                bucket_name=settings.S3_BUCKET_NAME
            )
        else:
            raise ValueError(f"Invalid storage backend '{settings.DEFAULT_STORAGE_BACKEND}'.")


    def get(self, name, backend_class, *args, **kwargs):
        try:
            StorageClass = import_string(backend_class)
        except Exception as exc:
            raise ValueError(f'Could not import storage class from "{backend_class}"') from exc
        if (
            not issubclass(StorageClass, FileSystemStorage)
            and not issubclass(StorageClass, S3Storage)
        ):
            raise ValueError(f'Invalid storage backend "{backend_class}"')

        instance = StorageClass(*args, **kwargs)
        return instance


storage_handler = StorageHandler()
default_storage = storage_handler.default_storage
