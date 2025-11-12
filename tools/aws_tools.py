import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from decouple import Config, RepositoryEnv
import os
from pathlib import Path


def download_s3_bucket(
        bucket_name,
        local_dir='./downloads',
        aws_access_key_id=None,
        aws_secret_access_key=None,
        region_name='us-east-2',
        prefix='',
        exclude_patterns=None,
        include_patterns=None
):
    """
    Download all files from an S3 bucket.

    Args:
        bucket_name (str): Name of the S3 bucket
        local_dir (str): Local directory to download files to
        aws_access_key_id (str, optional): AWS access key (uses default credentials if not provided)
        aws_secret_access_key (str, optional): AWS secret key
        region_name (str): AWS region name
        prefix (str, optional): Only download files with this prefix (folder path)
        exclude_patterns (list, optional): List of patterns to exclude (e.g., ['*.log', 'temp/*'])
        include_patterns (list, optional): List of patterns to include (e.g., ['*.jpg', '*.png'])

    Returns:
        dict: Summary of download operation

    Example:
        result = download_s3_bucket(
            bucket_name='my-wagtail-media',
            local_dir='./media',
            prefix='images/',
            exclude_patterns=['*.log', 'cache/*']
        )
    """

    print(f"========================================")
    print(f"S3 Bucket Download")
    print(f"========================================")
    print(f"Bucket: {bucket_name}")
    print(f"Local directory: {local_dir}")
    print(f"Prefix: {prefix if prefix else '(root)'}")
    print(f"========================================\n")

    # Create S3 client
    try:
        if aws_access_key_id and aws_secret_access_key:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name
            )
        else:
            # Use default credentials (from ~/.aws/credentials or environment variables)
            s3_client = boto3.client('s3', region_name=region_name)

        print("✓ Connected to S3")
    except NoCredentialsError:
        print("✗ AWS credentials not found!")
        return {
            'success': False,
            'error': 'No AWS credentials found. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables or pass them as parameters.'
        }
    except Exception as e:
        print(f"✗ Error connecting to S3: {e}")
        return {
            'success': False,
            'error': str(e)
        }

    # Create local directory
    Path(local_dir).mkdir(parents=True, exist_ok=True)

    downloaded_files = []
    skipped_files = []
    failed_files = []
    total_size = 0

    try:
        # List all objects in the bucket
        print(f"Listing objects in bucket '{bucket_name}'...\n")

        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

        for page in pages:
            if 'Contents' not in page:
                continue

            for obj in page['Contents']:
                s3_key = obj['Key']
                file_size = obj['Size']

                # Skip directories (keys ending with /)
                if s3_key.endswith('/'):
                    continue

                # Check exclude patterns
                if exclude_patterns and any(_matches_pattern(s3_key, pattern) for pattern in exclude_patterns):
                    skipped_files.append(s3_key)
                    print(f"⊝ Skipped (excluded): {s3_key}")
                    continue

                # Check include patterns
                if include_patterns and not any(_matches_pattern(s3_key, pattern) for pattern in include_patterns):
                    skipped_files.append(s3_key)
                    print(f"⊝ Skipped (not included): {s3_key}")
                    continue

                # Determine local file path
                if prefix and s3_key.startswith(prefix):
                    # Remove prefix from local path
                    relative_path = s3_key[len(prefix):]
                else:
                    relative_path = s3_key

                local_file_path = os.path.join(local_dir, relative_path)

                # Create subdirectories if needed
                local_file_dir = os.path.dirname(local_file_path)
                if local_file_dir:
                    Path(local_file_dir).mkdir(parents=True, exist_ok=True)

                # Download the file
                try:
                    print(f"↓ Downloading: {s3_key} ({_format_size(file_size)})")
                    s3_client.download_file(bucket_name, s3_key, local_file_path)
                    downloaded_files.append({
                        's3_key': s3_key,
                        'local_path': local_file_path,
                        'size': file_size
                    })
                    total_size += file_size
                    print(f"  ✓ Saved to: {local_file_path}")
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    print(f"  ✗ Failed: {error_code}")
                    failed_files.append({
                        's3_key': s3_key,
                        'error': str(e)
                    })
                except Exception as e:
                    print(f"  ✗ Failed: {e}")
                    failed_files.append({
                        's3_key': s3_key,
                        'error': str(e)
                    })

        # Summary
        print(f"\n{'=' * 50}")
        print(f"✓ Download Complete!")
        print(f"{'=' * 50}")
        print(f"Downloaded: {len(downloaded_files)} files ({_format_size(total_size)})")
        print(f"Skipped: {len(skipped_files)} files")
        print(f"Failed: {len(failed_files)} files")
        print(f"{'=' * 50}\n")

        return {
            'success': True,
            'downloaded_files': downloaded_files,
            'skipped_files': skipped_files,
            'failed_files': failed_files,
            'total_files': len(downloaded_files),
            'total_size': total_size,
            'local_directory': local_dir
        }

    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"\n✗ S3 Error: {error_code}")
        return {
            'success': False,
            'error': f"S3 Error: {error_code}",
            'downloaded_files': downloaded_files,
            'failed_files': failed_files
        }
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return {
            'success': False,
            'error': str(e),
            'downloaded_files': downloaded_files,
            'failed_files': failed_files
        }


def _matches_pattern(path, pattern):
    """Check if path matches a glob-style pattern"""
    import fnmatch
    return fnmatch.fnmatch(path, pattern)


def _format_size(bytes):
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} PB"


# Example usage
if __name__ == "__main__":
    config = Config(RepositoryEnv(".env.dev"))

    buckets = [config('AWS_STATIC_STORAGE_BUCKET_NAME'), config('AWS_MEDIA_STORAGE_BUCKET_NAME')]
    #buckets = [config('AWS_MEDIA_STORAGE_BUCKET_NAME')]

    for bucket_name in buckets:
        print(f"\n========================================")
        print(f"S3 Bucket Download: {bucket_name}")
        print(f"========================================")

        result = download_s3_bucket(
            bucket_name=bucket_name,
            local_dir='./downloads',
            aws_access_key_id=config('S3_ACCESS_KEY'),
            aws_secret_access_key=config('S3_SECRET_KEY'),
            region_name=config('AWS_S3_REGION_NAME'),
            prefix='',  # Download everything
        )

        if result['success']:
            print(f"\n✓ Successfully downloaded {result['total_files']} files")
            print(f"  Total size: {_format_size(result['total_size'])}")
            print(f"  Location: {result['local_directory']}")
        else:
            print(f"\n✗ Download failed: {result['error']}")