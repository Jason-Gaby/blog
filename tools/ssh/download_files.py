import os
import paramiko
from pathlib import Path
from decouple import Config, RepositoryEnv


def ssh_download_folder(
        host,
        username,
        remote_folder,
        local_folder,
        key_file=None,
        password=None,
        port=22,
        timeout=30
):
    """
    Downloads all files and subdirectories from a target remote folder to a local folder
    using SFTP. Creates local directories as needed.

    Args:
        host (str): IP address or hostname of the remote server
        username (str): SSH username
        remote_folder (str): Path to the remote folder containing files to download
        local_folder (str): Path to the target local folder
        key_file (str, optional): Path to SSH private key file (.pem)
        password (str, optional): SSH password
        port (int, optional): SSH port. Defaults to 22
        timeout (int, optional): Connection timeout. Defaults to 30

    Returns:
        dict: Result dictionary with status and list of downloaded files.
    """
    ssh_client = None
    sftp_client = None
    downloaded_files = []

    try:
        # 1. Initialize SSH client and connect
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_params = {
            'hostname': host,
            'port': port,
            'username': username,
            'timeout': timeout
        }

        if key_file:
            try:
                key = paramiko.RSAKey.from_private_key_file(key_file)
                connect_params['pkey'] = key
            except paramiko.ssh_exception.SSHException:
                # Try DSSKey if RSAKey fails
                key = paramiko.DSSKey.from_private_key_file(key_file)
                connect_params['pkey'] = key
        elif password:
            connect_params['password'] = password
        else:
            raise ValueError("Either key_file or password must be provided")

        print(f"Connecting to {host}...")
        ssh_client.connect(**connect_params)
        print("✓ Connected successfully!")

        # 2. Open SFTP connection
        sftp_client = ssh_client.open_sftp()

        # Ensure the local base folder exists
        local_folder_path = Path(local_folder)
        local_folder_path.mkdir(parents=True, exist_ok=True)
        print(f"Ensured local target folder exists: {local_folder_path.resolve()}")

        # 3. Walk through the remote folder structure
        print(f"Starting download from {remote_folder} to {local_folder}...")

        # We'll use a recursive function to walk the remote directory
        def remote_walk_and_download(remote_path):
            try:
                # Get contents of the current remote directory
                for item in sftp_client.listdir_attr(remote_path):
                    remote_file_path = os.path.join(remote_path, item.filename).replace("\\", "/")

                    # Calculate the relative path from the base remote_folder
                    relative_path = os.path.relpath(remote_file_path, remote_folder).replace("\\", "/")

                    # Calculate the corresponding local path
                    local_file_path = local_folder_path / relative_path

                    if item.filename in ('.', '..'):
                        continue

                    if item.st_mode is not None and (item.st_mode & 0o40000):  # Check if it's a directory
                        # Create the local directory and recurse
                        local_file_path.mkdir(parents=True, exist_ok=True)
                        remote_walk_and_download(remote_file_path)
                    else:
                        # Download the file
                        print(f"  Downloading: {relative_path} -> {local_file_path.resolve()}")
                        sftp_client.get(remote_file_path, str(local_file_path))
                        downloaded_files.append(str(local_file_path))

            except FileNotFoundError:
                raise FileNotFoundError(f"Remote folder not found: {remote_path}")

        # Start the recursive download
        remote_walk_and_download(remote_folder)

        print(f"✓ Download complete. Total files downloaded: {len(downloaded_files)}")

        return {
            'success': True,
            'downloaded_count': len(downloaded_files),
            'downloaded_files': downloaded_files,
            'remote_folder': remote_folder,
            'local_folder': str(local_folder_path.resolve())
        }

    except paramiko.AuthenticationException:
        print("✗ Authentication failed!")
        return {
            'success': False,
            'error': 'Authentication failed'
        }
    except FileNotFoundError as fnf_err:
        print(f"✗ File not found: {fnf_err}")
        return {
            'success': False,
            'error': str(fnf_err)
        }
    except paramiko.SSHException as ssh_err:
        print(f"✗ SSH error: {ssh_err}")
        return {
            'success': False,
            'error': f'SSH error: {str(ssh_err)}'
        }
    except Exception as e:
        print(f"✗ Error: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        # Clean up connections
        if sftp_client:
            sftp_client.close()
        if ssh_client:
            ssh_client.close()
            print("Connection closed")


# ---

if __name__ == "__main__":
    # Assuming .env.dev contains EC2_HOSTNAME, EC2_USER, and SSH_KEY_PATH
    # For testing, ensure your remote server has files in /tmp/upload/
    config = Config(RepositoryEnv(".env.dev"))

    # IMPORTANT: Replace these with your actual connection details
    remote_folder_to_download = "/tmp/downloads/"
    local_target_folder = "./downloads/"  # Downloads will go here

    result_download = ssh_download_folder(
        host=config('EC2_HOSTNAME'),
        username=config('EC2_USER'),
        remote_folder=remote_folder_to_download,
        local_folder=local_target_folder,
        key_file=config('SSH_KEY_PATH'),
    )

    if result_download['success']:
        print(f"\n{'=' * 50}")
        print(f"✓ SUCCESS! Downloaded {result_download['downloaded_count']} files.")
        print(f"{'=' * 50}")
        print(f"Local Path: {result_download['local_folder']}")
        print("Downloaded files list:")
        for f in result_download['downloaded_files']:
            print(f"  - {f}")
    else:
        print(f"\n{'=' * 50}")
        print(f"✗ FAILED!")
        print(f"{'=' * 50}")
        print(f"Error: {result_download['error']}")