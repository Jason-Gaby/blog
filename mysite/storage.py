from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    bucket_name = settings.AWS_STATIC_STORAGE_BUCKET_NAME
    location = 'static'


class PublicMediaStorage(S3Boto3Storage):
    bucket_name = settings.AWS_MEDIA_STORAGE_BUCKET_NAME
    location = 'media'
    file_overwrite = False