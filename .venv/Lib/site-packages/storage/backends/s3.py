import tempfile
import mimetypes
from datetime import datetime, timezone, timedelta

import boto3
from botocore.exceptions import ClientError

from storage.base import Storage
from storage.exceptions import StorageError
from storage.files import File, ContentFile
from storage.conf import settings




class S3Storage(Storage):

    def __init__(
        self,
        bucket_name,
        endpoint_url=None,
        upload_options={},
        access_key_id=None,
        secret_access_key=None,
    ):
        if not endpoint_url:
            endpoint_url = settings.S3_ENDPOINT_URL
        if not access_key_id:
            access_key_id = settings.S3_ACCESS_KEY_ID
        if not secret_access_key:
            secret_access_key = settings.S3_SECRET_ACCESS_KEY

        self.bucket_name = bucket_name
        self.client = boto3.client(
            service_name='s3',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            endpoint_url=endpoint_url,
        )
        self.upload_options = upload_options


    def _save(self, name, content, content_type=None, encoding='utf-8'):
        options = self.upload_options.copy()

        if content_type is None:
            content_type, _ = mimetypes.guess_type(name)

        if content_type:
            options['ContentType'] = content_type

        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=name,
                Body=content,
                **options,
            )
        except ClientError as e:
            raise StorageError('Error uploading file to S3') from e


    def _open(self, name, mode='rb'):
        """
        Open a file from the S3 bucket.

        :param name: The name of the file in the bucket.
        :param mode: The mode to open the file in (default: "rb").
        :return: A file-like object.
        """
        if mode not in ('r', 'rb'):
            raise ValueError("S3Storage only supports read modes: 'r' and 'rb'")
        try:
            obj = self.client.get_object(
                Bucket=self.bucket_name,
                Key=name,
            )
        except ClientError as err:
            raise FileNotFoundError(f'File does not exist: {name}')

        content = obj["Body"].read()

        if "b" not in mode:
            content = content.decode()

        return ContentFile(content, name=name)


    def delete(self, name):
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=name)
        except ClientError as err:
            if err.response['ResponseMetadata']['HTTPStatusCode'] == 404:
                # Not an error to delete something that does not exist
                return
            raise StorageError('Error deleting file from S3') from err


    def get_pages(self, prefix=None):
        if not prefix:
            prefix = ''
        if not isinstance(prefix, str):
            raise TypeError('"prefix" kwarg must be a string')
        paginator = self.client.get_paginator('list_objects_v2')
        pagination_kwargs = {
            'Bucket': self.bucket_name,
            'Prefix': prefix,
        }
        for page in paginator.paginate(**pagination_kwargs):
            yield page


    def get_objects(self, prefix=None):
        """
        Usage::

            objects = default_storage.get_objects(prefix='optional_prefix/')
            for object in objects:
                print(object)
                #
                # Will print something similar to:
                # {
                #     'Key': 'filename.jpg',
                #     'LastModified': datetime.datetime(2023, 5, 24, 16, 16, 38, 377000, tzinfo=tzutc()),
                #     'ETag': '123123',
                #     'Size': 129581,
                # }
        """
        pages = self.get_pages(prefix=prefix)
        for page in pages:
            contents = page.get('Contents', [])
            for object in contents:
                yield object


    def _delete_older_than(self, delta=None, older_than=None, prefix=None):
        if delta:
            if not isinstance(delta, timedelta):
                raise TypeError('"delta" kwarg must be a timedelta instance')
        if older_than:
            if not isinstance(older_than, datetime):
                raise TypeError('"older_than" kwarg must be a datetime instance')

        if older_than and delta:
            raise ValueError('You cannot provide both "delta" and "older_than" kwargs')
        if not older_than and not delta:
            raise ValueError(
                'You must provide a value for the "delta" '
                'or "older_than" kwargs'
            )

        now = datetime.now(tz=timezone.utc)
        if not older_than:
            older_than = now - delta

        old_files = []
        objects = self.get_objects(prefix=prefix)
        for object in objects:
            """
            Example of ``object``::

                {
                    'Key': 'filename.jpg',
                    'LastModified': datetime.datetime(2023, 5, 24, 16, 16, 38, 377000, tzinfo=tzutc()),
                    'ETag': '123123',
                    'Size': 129581,
                }
            """
            # Cannot delete more than 1000 objects
            # at a time via "delete_objects"
            if len(old_files) == 1000:
                break

            last_modified = object['LastModified']
            key = object['Key']

            if last_modified:
                if last_modified < older_than:
                    old_files.append({'Key': key})

        if not old_files:
            return

        to_delete = {'Objects': old_files}
        response = self.client.delete_objects(
            Bucket=self.bucket_name,
            Delete=to_delete,
        )
        deleted = response['Deleted']
        return deleted


    def delete_older_than(self, *args, **kwargs):
        """
        Usage::

            from datetime import datetime, timedelta
            from storage import default_storage


            older_than = datetime.fromisoformat('2023-05-28T00:00:00.000000+00:00')
            deleted = default_storage.delete_older_than(
                older_than=older_than,
                prefix='myfiles/',
            )

        Or use a ``timedelta`` instead::

            delta = timedelta(days=30)
            deleted = default_storage.delete_older_than(delta=delta)
        """
        try:
            return self._delete_older_than(*args, **kwargs)
        except ClientError as e:
            raise StorageError(
                'Error deleting objects from storage older than delta'
            ) from e


    def exists(self, name) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=name)
            return True
        except ClientError as e:
            return False


    def size(self, name):
        try:
            obj = self.client.head_object(Bucket=self.bucket_name, Key=name)
            return obj['ContentLength']
        except ClientError as e:
            raise StorageError('Error getting file size from S3') from e


    def url(self, name):
        return f'{settings.S3_ENDPOINT_URL}/{name}'
