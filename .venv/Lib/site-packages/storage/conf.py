from decouple import config




class Settings:
    DEFAULT_STORAGE_BACKEND = config('DEFAULT_STORAGE_BACKEND', default='storage.backends.filesystem.FileSystemStorage')
    BASE_PATH = config('STORAGE_BASE_PATH', default='media/')
    FILE_PERMISSIONS = config('STORAGE_FILE_PERMISSIONS', default='0o644')
    FILE_PERMISSIONS = int(FILE_PERMISSIONS, 8)
    BASE_URL = config('STORAGE_BASE_URL', default='/media/')

    S3_BUCKET_NAME = config('S3_BUCKET_NAME', default=None)
    S3_ENDPOINT_URL = config('S3_ENDPOINT_URL', default=None)
    # https://{S3_BUCKET_NAME}.s3.amazonaws.com/{S3_BUCKET_NAME}
    S3_ACCESS_KEY_ID = config('S3_ACCESS_KEY_ID', default='')
    S3_SECRET_ACCESS_KEY = config('S3_SECRET_ACCESS_KEY', default='')


settings = Settings
