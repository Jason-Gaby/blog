import os
import paramiko
from pathlib import Path
from decouple import Config, RepositoryEnv

def ssh_upload_folder(
        host,
        username,
        local_folder,
        remote_folder,
        key_file=None,
        password=None,
        port=22,
        timeout=30
):
    """
    Uploads all files and subdirectories from a local folder to a target remote folder
    using SFTP. Creates remote directories as needed.

    Args:
        host (str): IP address or hostname of the remote server
        username (str): SSH username
        local_folder (str): Path to the local folder containing files to upload
        remote_folder (str): Path to the target folder on the remote server
        key_file (str, optional): Path to SSH private key file (.pem)
        password (str, optional): SSH password
        port (int, optional): SSH port. Defaults to 22
        timeout (int, optional): Connection timeout. Defaults to 30

    Returns:
        dict: Result dictionary with status and list of uploaded files.
    """
    ssh_client = None
    sftp_client = None
    uploaded_files = []

    # Helper function to create remote directory using SSH
    def remote_mkdir_p(client, remote_path):
        """Ensures remote directory exists, similar to mkdir -p."""
        command = f"mkdir -p {remote_path}"
        stdin, stdout, stderr = client.exec_command(command)
        if stdout.channel.recv_exit_status() != 0:
            raise paramiko.SSHException(f"Failed to create remote directory {remote_path}: {stderr.read().decode()}")

    try:
        # Validate local folder existence
        local_folder = os.path.abspath(local_folder)
        if not os.path.isdir(local_folder):
            raise FileNotFoundError(f"Local folder not found or is not a directory: {local_folder}")

        # Initialize SSH client
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Prepare connection parameters
        connect_params = {
            'hostname': host,
            'port': port,
            'username': username,
            'timeout': timeout
        }

        # Add authentication
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

        # Connect to the server
        print(f"Connecting to {host}...")
        ssh_client.connect(**connect_params)
        print("✓ Connected successfully!")

        # Open SFTP connection
        sftp_client = ssh_client.open_sftp()

        # Ensure the remote base folder exists
        remote_mkdir_p(ssh_client, remote_folder)
        print(f"Ensured remote target folder exists: {remote_folder}")

        # Walk through the local folder
        print(f"Starting upload from {local_folder} to {remote_folder}...")
        for root, dirs, files in os.walk(local_folder):
            # Calculate the relative path from the base local_folder
            relative_path = os.path.relpath(root, local_folder)

            # Calculate the corresponding remote path for the current root
            remote_current_dir = os.path.join(remote_folder, relative_path).replace("\\",
                                                                                    "/")  # Use forward slashes for remote paths

            # 1. Create subdirectories on the remote server
            for dir_name in dirs:
                remote_sub_dir = os.path.join(remote_current_dir, dir_name).replace("\\", "/")
                # Ensure directory exists before uploading files to it
                remote_mkdir_p(ssh_client, remote_sub_dir)

            # 2. Upload files
            for file_name in files:
                local_file_path = os.path.join(root, file_name)
                remote_file_path = os.path.join(remote_current_dir, file_name).replace("\\", "/")

                print(f"  Uploading: {relative_path}/{file_name} -> {remote_file_path}")
                sftp_client.put(local_file_path, remote_file_path)
                uploaded_files.append(remote_file_path)

        print(f"✓ Upload complete. Total files uploaded: {len(uploaded_files)}")

        return {
            'success': True,
            'uploaded_count': len(uploaded_files),
            'uploaded_files': uploaded_files,
            'local_folder': local_folder,
            'remote_folder': remote_folder
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


# Example usage
if __name__ == "__main__":
    # Configuration is loaded or mocked here
    config = Config(RepositoryEnv(".env.dev"))

    # IMPORTANT: Replace these with your actual connection details for a real test
    local_folder = "./uploads/"
    remote_folder = "/tmp/upload/"

    result = ssh_upload_folder(
        host=config('EC2_HOSTNAME'),
        username=config('EC2_USER'),
        local_folder=local_folder,
        remote_folder=remote_folder,
        key_file=config('SSH_KEY_PATH'),
    )

    if result['success']:
        print(f"\n{'=' * 50}")
        print(f"✓ SUCCESS! Uploaded {result['uploaded_count']} files.")
        print(f"{'=' * 50}")
        print(f"Remote Path: {result['remote_folder']}")
        print("Uploaded files list:")
        for f in result['uploaded_files']:
            print(f"  - {f}")
    else:
        print(f"\n{'=' * 50}")
        print(f"✗ FAILED!")
        print(f"{'=' * 50}")
        print(f"Error: {result['error']}")