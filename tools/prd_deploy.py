from decouple import Config, RepositoryEnv
from tools.ssh.upload_and_run_bash_script import ssh_upload_script_execute_and_download
from tools.ssh.upload_files import ssh_upload_folder

import subprocess
import shutil
import os
from pathlib import Path

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_local_command(command, description):
    """Runs a shell command locally and checks the exit status."""
    print(f"\n--- Running: {description} ---")
    try:
        # Execute command, capturing output
        result = subprocess.run(
            command,
            check=True,  # Raise CalledProcessError if return code is non-zero
            shell=True,
            capture_output=True,
            text=True
        )
        print("✓ Success.")
        if result.stdout:
            print(f"STDOUT:\n{result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"✗ Failure: {description} failed.")
        print(f"STDERR:\n{e.stderr.strip()}")
        raise
    except FileNotFoundError:
        print(f"✗ Error: Command not found. Check if '{command.split()[0]}' is in PATH or if VENV path is correct.")
        raise


def copy_and_overwrite_any(source_path, destination_path):
    """
    Copies a file OR the contents of a directory (source_path)
    into a target directory (destination_path), overwriting existing files.
    """
    source_path = Path(source_path)
    destination_path = Path(destination_path)

    print(f"\n--- Copying '{source_path}' to '{destination_path}' (Overwriting) ---")

    if not source_path.exists():
        print(f"Error: Source path '{source_path}' not found.")
        return

    # --- 1. Handle Case: Source is a FILE ---
    if source_path.is_file():
        # The destination must be a directory where the file will be placed.
        os.makedirs(destination_path, exist_ok=True)

        dest_file = destination_path / source_path.name
        shutil.copy2(str(source_path), str(dest_file))
        print(f"Copied file: {source_path} -> {dest_file}")
        print("✓ Copy complete.")
        return

    # --- 2. Handle Case: Source is a FOLDER (Original Logic) ---

    # Create the destination root directory if it doesn't exist
    os.makedirs(destination_path, exist_ok=True)

    # Walk through the source directory tree
    for root, dirs, files in os.walk(source_path):
        # Construct the relative path from the source_path
        relative_path = Path(root).relative_to(source_path)

        # Construct the full destination path for the current directory
        dest_path = destination_path / relative_path

        # Create necessary subdirectories in the destination
        for d in dirs:
            os.makedirs(dest_path / d, exist_ok=True)

        # Copy files, overwriting if necessary
        for f in files:
            source_file = Path(root) / f
            dest_file = dest_path / f

            # copy2 is preferred as it attempts to preserve metadata (timestamps)
            shutil.copy2(str(source_file), str(dest_file))
            print(f"Copied: {source_file} -> {dest_file}")

    print("✓ Copy and overwrite complete.")

if __name__ == "__main__":
    config = Config(RepositoryEnv(".env.dev"))

    # Collect static files
    collectstatic_cmd = f"python manage.py collectstatic --noinput"
    run_local_command(collectstatic_cmd, "Django collectstatic")

    # Copy local files into upload folder
    files = ['static', '.env.production', '.env.base']
    for file in files:
        copy_and_overwrite_any(f'./{file}', f'./upload/{file}')

    # Upload files
    ssh_upload_folder(
        host=config('EC2_HOSTNAME'),
        username=config('EC2_USER'),
        local_folder=f'{ROOT_DIR}/upload/',
        remote_folder='/tmp/upload/',
        key_file=config('SSH_KEY_PATH'),
    )

    # Run build bash script
    bash_script_name = 'prd_deploy.sh'
    host = config('EC2_HOSTNAME'),
    username = config('EC2_USER'),
    local_script_path = f'{ROOT_DIR}/tools/bash/{bash_script_name}',
    key_file = config('SSH_KEY_PATH'),

    venv_path = config('VENV_PATH')
    project_root = config('PROJECT_ROOT')
    script_args = f'{venv_path} {project_root}'

    result = ssh_upload_script_execute_and_download(
        host=config('EC2_HOSTNAME'),
        username=config('EC2_USER'),
        local_script_path=f'{ROOT_DIR}/tools/bash/{bash_script_name}',
        key_file=config('SSH_KEY_PATH'),
        script_args=script_args,
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