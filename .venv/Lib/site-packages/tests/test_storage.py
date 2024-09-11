import os
import tempfile
from io import BytesIO
from unittest.mock import patch

import pytest
import boto3
import botocore.exceptions
from moto import mock_s3

from storage.backends import FileSystemStorage, S3Storage
from storage.exceptions import StorageError
from storage.conf import settings




@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir




@pytest.fixture
def mock_s3_bucket():
    with mock_s3():
        bucket_name = 'my-test-bucket'
        boto3.client('s3').create_bucket(Bucket=bucket_name)
        yield bucket_name




# @pytest.fixture(autouse=True)
# def mock_settings():
#     with patch.object(settings, 'S3_ENDPOINT_URL', None):
#         with patch.object(settings, 'S3_ACCESS_KEY_ID', 'mock_secret'):
#             with patch.object(settings, 'S3_SECRET_ACCESS_KEY', 'mock_secret'):
#                 yield




def test_filesystem_storage(temp_dir):
    storage = FileSystemStorage(base_path=temp_dir)
    file_name = 'test.txt'
    file_content = b'Hello, world!'

    storage.save(file_name, file_content)
    assert os.path.exists(os.path.join(temp_dir, file_name))
    assert storage.exists(file_name)
    assert storage.size(file_name) == len(file_content)
    assert storage.url(file_name) == f'/media/{file_name}'

    storage.delete(file_name)
    assert not os.path.exists(os.path.join(temp_dir, file_name))




@pytest.mark.parametrize('file_content', [
    b'Hello, world!',
    'Hello, world!',
    b'',
    '',
])
def test_s3_storage(mock_s3_bucket, file_content):
    storage = S3Storage(bucket_name=mock_s3_bucket)
    file_name = 'test.txt'

    storage.save(file_name, file_content)
    assert storage.exists(file_name)
    assert storage.exists(file_name)
    assert storage.size(file_name) == len(file_content)

    storage.delete(file_name)
    assert not storage.exists(file_name)
    storage.delete(file_name)




@pytest.mark.parametrize('storage_class,init_kwargs', [
    (FileSystemStorage, {'base_path': temp_dir}),
    (S3Storage, {'bucket_name': mock_s3_bucket})
])
def test_open_method(temp_dir, mock_s3_bucket, storage_class, init_kwargs):
    file_name = 'testfile.txt'
    file_content = b'Hello, World!'

    if storage_class == FileSystemStorage:
        init_kwargs['base_path'] = temp_dir
    else:
        init_kwargs['bucket_name'] = mock_s3_bucket

    storage_instance = storage_class(**init_kwargs)
    storage_instance.save(file_name, file_content)

    with storage_instance.open(file_name, mode='rb') as f:
        content = f.read()
        assert content == file_content

    if storage_class == S3Storage:
        # Test opening the file in text mode
        with storage_instance.open(file_name, mode='r') as f:
            content = f.read()
            assert content == file_content.decode()




def test_s3storage_open_nonexistent_file_error(mock_s3_bucket):
    storage = S3Storage(bucket_name=mock_s3_bucket)
    file_name = "nonexistent.txt"

    with pytest.raises(FileNotFoundError):
        with storage.open(file_name, mode="rb") as f:
            pass




def test_s3storage_save_storage_error(mock_s3_bucket):
    storage = S3Storage(bucket_name=mock_s3_bucket)
    file_name = "nonexistent.txt"

    # Simulate a ClientError when calling put_object
    with patch.object(storage.client, "put_object") as mock_put_object:
        mock_put_object.side_effect = botocore.exceptions.ClientError(
            {"Error": {"Code": "SomeErrorCode", "Message": "Some error message"}},
            "PutObject"
        )

        with pytest.raises(StorageError):
            storage.save(file_name, b'Content')
