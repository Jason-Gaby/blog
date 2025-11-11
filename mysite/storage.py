from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage
from django.contrib.staticfiles.finders import FileSystemFinder
import os


class StaticStorage(S3Boto3Storage):
    bucket_name = settings.AWS_STATIC_STORAGE_BUCKET_NAME
    location = 'static'


class PublicMediaStorage(S3Boto3Storage):
    bucket_name = settings.AWS_MEDIA_STORAGE_BUCKET_NAME
    location = 'media'
    file_overwrite = False


class NonRecursiveFileSystemFinder(FileSystemFinder):
    """
    A StaticFiles Finder that only looks at the top level of directories
    listed in STATICFILES_DIRS, preventing recursive collection.
    """

    def list(self, ignored_patterns):
        """
        List all files in all locations that are not in ignored_patterns,
        without recursing into subdirectories.
        """
        # Iterate over the paths defined in STATICFILES_DIRS (self.locations)
        for prefix, root in self.locations:
            if not os.path.isdir(root):
                continue

            # Use os.listdir() instead of os.walk() to avoid recursion
            for name in os.listdir(root):
                path = os.path.join(root, name)

                # Crucial check: Only yield if it is a file, skip directories
                if os.path.isfile(path):
                    # yield the relative path and the finder instance
                    yield os.path.join(prefix, name), self