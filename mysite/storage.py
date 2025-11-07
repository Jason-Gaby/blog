from decouple import config
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    bucket_name = config("AWS_STATIC_STORAGE_BUCKET_NAME")
    location = 'static'
    default_acl = 'public-read'


class PublicMediaStorage(S3Boto3Storage):
    bucket_name = config("AWS_MEDIA_STORAGE_BUCKET_NAME")
    location = 'media'
    default_acl = 'public-read'
    file_overwrite = False