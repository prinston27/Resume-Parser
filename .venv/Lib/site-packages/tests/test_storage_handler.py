import unittest
from unittest.mock import patch

import pytest

from storage.handler import StorageHandler
from storage.backends import FileSystemStorage, S3Storage
from storage.conf import Settings




class TestStorageHandler(unittest.TestCase):

    def test_filesystem_storage_initialization(self):
        with patch.multiple(Settings, DEFAULT_STORAGE_BACKEND="storage.backends.filesystem.FileSystemStorage"):
            storage_handler = StorageHandler()
            self.assertIsInstance(storage_handler.default_storage, FileSystemStorage)


    def test_s3_storage_initialization(self):
        patches = {
            "DEFAULT_STORAGE_BACKEND": "storage.backends.s3.S3Storage",
            "S3_BUCKET_NAME": "test-bucket",
        }
        with patch.multiple(Settings, **patches):
            storage_handler = StorageHandler()
            self.assertIsInstance(storage_handler.default_storage, S3Storage)


    def test_invalid_storage_backend(self):
        with patch.multiple(Settings, DEFAULT_STORAGE_BACKEND="storage.backends.InvalidStorage"):
            with self.assertRaises(ValueError):
                StorageHandler()


    def test_missing_s3_bucket_name(self):
        patches = {
            "DEFAULT_STORAGE_BACKEND": "storage.backends.s3.S3Storage",
            "S3_BUCKET_NAME": None,
        }
        with patch.multiple(Settings, **patches):
            with self.assertRaises(ValueError):
                StorageHandler()




if __name__ == "__main__":
    unittest.main()
