from decouple import Config, RepositoryEnv
from tools.ssh.upload_and_run_bash_script import ssh_upload_script_execute_and_download
from tools.ssh.upload_files import ssh_upload_folder
from definitions import ENV_DIR

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


def copy_and_overwrite_any(source_path, destination_root):
    """
    source_path: The file or folder to copy.
    destination_root: The folder where the source should be placed.
    """
    source = Path(source_path)
    dest_root = Path(destination_root)

    if not source.exists():
        print(f"Error: Source '{source}' not found.")
        return

    # --- 1. Handle Case: Source is a FILE ---
    if source.is_file():
        # Ensure the destination directory exists (e.g., /tmp/upload/.env/)
        dest_root.mkdir(parents=True, exist_ok=True)

        # Define the final file path (e.g., /tmp/upload/.env/.env.base)
        dest_file = dest_root / source.name

        shutil.copy2(source, dest_file)
        print(f"Copied file: {source} -> {dest_file}")

    # --- 2. Handle Case: Source is a FOLDER ---
    else:
        # Define the target folder (e.g., /tmp/upload/static)
        dest_folder = dest_root / source.name

        # dirs_exist_ok=True allows merging/overwriting existing folders
        shutil.copytree(source, dest_folder, dirs_exist_ok=True)
        print(f"Copied folder: {source} -> {dest_folder}")


if __name__ == "__main__":
    config = Config(RepositoryEnv(os.path.join(ENV_DIR, ".env.dev")))

    # Collect static files
    collectstatic_cmd = f"python manage.py collectstatic --noinput"
    run_local_command(collectstatic_cmd, "Django collectstatic")

    # The base folder where you want everything to end up
    UPLOAD_DIR = "./uploads"

    # List of items to copy
    # We use a tuple (source, relative_dest_subfolder)
    items_to_copy = [
        ('static', ''),  # Goes to ./upload/static
        ('.env/.env.production', '.env'),  # Goes to ./upload/.env/.env.production
        ('.env/.env.base', '.env')  # Goes to ./upload/.env/.env.base
    ]

    for src, subfolder in items_to_copy:
        target_dir = Path(UPLOAD_DIR) / subfolder
        copy_and_overwrite_any(src, target_dir)

    # Upload files
    ssh_upload_folder(
        host=config('EC2_HOSTNAME'),
        username=config('EC2_USER'),
        local_folder=f'{ROOT_DIR}/uploads/',
        remote_folder='/tmp/uploads/',
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
    content_root = config('CONTENT_ROOT_DIR')
    script_args = f'{venv_path} {project_root} {content_root}'

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