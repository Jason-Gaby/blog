from decouple import Config, RepositoryEnv
import os
from pathlib import Path
import paramiko

def ssh_upload_script_execute_and_download(
        host,
        username,
        local_script_path,
        remote_file_path,
        local_download_path,
        key_file=None,
        password=None,
        port=22,
        timeout=30,
        script_args=None,
        remote_script_dir="/tmp",
        cleanup_script=True
):
    """
    Upload a bash script to AWS VM, execute it, and download the resulting file.

    Args:
        host (str): IP address or hostname of the AWS VM
        username (str): SSH username (e.g., 'ec2-user', 'ubuntu')
        local_script_path (str): Path to local bash script to upload
        remote_file_path (str): Path to the output file on remote server
        local_download_path (str): Local path where the file should be saved
        key_file (str, optional): Path to SSH private key file (.pem)
        password (str, optional): SSH password
        port (int, optional): SSH port. Defaults to 22
        timeout (int, optional): Connection timeout. Defaults to 30
        script_args (str, optional): Arguments to pass to the script
        remote_script_dir (str, optional): Directory to upload script to. Defaults to /tmp
        cleanup_script (bool, optional): Delete script after execution. Defaults to True

    Returns:
        dict: Result dictionary with status, outputs, and file path

    Example:
        result = ssh_upload_script_execute_and_download(
            host='ec2-xx-xxx-xxx-xx.compute-1.amazonaws.com',
            username='ec2-user',
            local_script_path='./scripts/process_data.sh',
            remote_file_path='/home/ec2-user/output/report.csv',
            local_download_path='./downloads/report.csv',
            key_file='/path/to/your-key.pem',
            script_args='--mode production --output report.csv'
        )
    """
    ssh_client = None
    sftp_client = None

    try:
        # Validate local script exists
        if not os.path.exists(local_script_path):
            raise FileNotFoundError(f"Local script not found: {local_script_path}")

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

        # Open SFTP connection for file upload
        sftp_client = ssh_client.open_sftp()

        # Determine remote script path
        script_filename = os.path.basename(local_script_path)
        remote_script_path = f"{remote_script_dir}/{script_filename}"

        # Upload the script
        print(f"Uploading script {local_script_path} to {remote_script_path}...")
        sftp_client.put(local_script_path, remote_script_path)
        print("✓ Script uploaded successfully!")

        # Make script executable
        print("Making script executable...")
        stdin, stdout, stderr = ssh_client.exec_command(f"chmod +x {remote_script_path}")
        stdout.channel.recv_exit_status()  # Wait for command to complete
        print("✓ Script is now executable")

        # Build command with arguments if provided
        if script_args:
            command = f"{remote_script_path} {script_args}"
        else:
            command = remote_script_path

        # Execute the script
        print(f"Executing script: {command}")
        stdin, stdout, stderr = ssh_client.exec_command(command)

        # Wait for script to complete and capture output
        exit_status = stdout.channel.recv_exit_status()
        stdout_output = stdout.read().decode('utf-8')
        stderr_output = stderr.read().decode('utf-8')

        print(f"Script exit status: {exit_status}")

        if stdout_output:
            print(f"STDOUT:\n{stdout_output}")
        if stderr_output:
            print(f"STDERR:\n{stderr_output}")

        # Check if script executed successfully
        if exit_status != 0:
            result = {
                'success': False,
                'exit_status': exit_status,
                'stdout': stdout_output,
                'stderr': stderr_output,
                'remote_script_path': remote_script_path,
                'error': 'Script execution failed'
            }

            # Cleanup even on failure if requested
            if cleanup_script:
                try:
                    sftp_client.remove(remote_script_path)
                    print(f"✓ Cleaned up script: {remote_script_path}")
                except:
                    pass

            return result

        print("✓ Script executed successfully!")

        # Download the output file
        print(f"Downloading file from {remote_file_path}...")

        # Create local directory if it doesn't exist
        local_dir = os.path.dirname(local_download_path)
        if local_dir:
            Path(local_dir).mkdir(parents=True, exist_ok=True)

        # Download the file
        sftp_client.get(remote_file_path, local_download_path)
        print(f"✓ File downloaded successfully to {local_download_path}")

        # Get file stats
        file_stats = sftp_client.stat(remote_file_path)

        # Cleanup script if requested
        if cleanup_script:
            try:
                sftp_client.remove(remote_script_path)
                print(f"✓ Cleaned up script: {remote_script_path}")
            except Exception as e:
                print(f"⚠ Could not cleanup script: {e}")

        return {
            'success': True,
            'exit_status': exit_status,
            'stdout': stdout_output,
            'stderr': stderr_output,
            'local_file_path': local_download_path,
            'remote_file_path': remote_file_path,
            'remote_script_path': remote_script_path,
            'file_size': file_stats.st_size,
            'script_cleaned_up': cleanup_script
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
    config = Config(RepositoryEnv(".env.dev"))
    bash_script_name = 'db_dump_json.sh'
    output_file_name = 'data.json'
    remote_file_path = f'/tmp/{output_file_name}'
    venv_path = config('VENV_PATH')
    project_root = config('PROJECT_ROOT')

    result = ssh_upload_script_execute_and_download(
        host=config('EC2_HOSTNAME'),
        username=config('EC2_USER'),
        local_script_path=f'./tools/bash/{bash_script_name}',
        remote_file_path=remote_file_path,
        local_download_path=f'./downloads/{output_file_name}',
        key_file=config('SSH_KEY_PATH'),
        script_args=f'{venv_path} {project_root} {remote_file_path}'
    )

    if result['success']:
        print(f"\n{'=' * 50}")
        print(f"✓ SUCCESS!")
        print(f"{'=' * 50}")
        print(f"Local file: {result['local_file_path']}")
        print(f"File size: {result['file_size']} bytes")
        print(f"Script cleaned up: {result['script_cleaned_up']}")
    else:
        print(f"\n{'=' * 50}")
        print(f"✗ FAILED!")
        print(f"{'=' * 50}")
        print(f"Error: {result['error']}")
        if 'stderr' in result:
            print(f"Error output:\n{result['stderr']}")