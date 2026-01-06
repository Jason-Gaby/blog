from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage, S3ManifestStaticStorage


class StaticStorage(S3ManifestStaticStorage):
    bucket_name = settings.AWS_STATIC_STORAGE_BUCKET_NAME
    location = 'static'
    default_acl = 'public-read'

    # This overrides the global for static files
    def get_object_parameters(self, name):
        params = super().get_object_parameters(name)
        # Set static files to 1 hour or no-cache instead of 24 hours
        # This solves ths issue with loading the "Preview" on Wagtail Admin pages during edit.
        # The body section wouldn't load after 24-hours.
        params['CacheControl'] = 'max-age=31536000, public, immutable'
        return params


class PublicMediaStorage(S3Boto3Storage):
    bucket_name = settings.AWS_MEDIA_STORAGE_BUCKET_NAME
    location = 'media'
    file_overwrite = False
