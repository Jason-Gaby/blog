import argparse
from decouple import Config, RepositoryEnv
import subprocess
import shutil
import stat
import time
import os
from pathlib import Path

from tools.ssh.upload_and_run_bash_script import ssh_upload_script_execute_and_download
from tools.ssh.upload_files import ssh_upload_folder
from definitions import ENV_DIR

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_local_command(command, description, cwd=None):
    """Runs a shell command locally and checks the exit status."""
    print(f"\n--- Running: {description} ---")
    try:
        # Execute command, capturing output
        result = subprocess.run(
            command,
            check=True,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
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

def force_remove_readonly(func, path, excinfo):
    """
    Error handler for shutil.rmtree to handle read-only files.
    """
    # Clear the read-only bit and retry the removal
    os.chmod(path, stat.S_IWRITE)
    func(path)

def safe_rmtree(path):
    if os.path.exists(path):
        try:
            shutil.rmtree(path, onerror=force_remove_readonly)
        except Exception:
            # Sometimes Windows needs a moment to release a lock
            time.sleep(0.5)
            shutil.rmtree(path, ignore_errors=True)

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Wagtail Production Deploy Tool")

    # Flags to SKIP parts of the process
    parser.add_argument('--skip-static', action='store_true', help="Skip Django collectstatic")
    parser.add_argument('--skip-upload', action='store_true', help="Skip SSH folder upload")
    parser.add_argument('--skip-script', action='store_true', help="Skip remote bash script execution")
    parser.add_argument('--git-only', action='store_true', help="Run only a remote git pull.")
    args = parser.parse_args()

    # Initialize config files
    dev_config = Config(RepositoryEnv(os.path.join(ROOT_DIR, ENV_DIR, ".env.dev")))
    config = Config(RepositoryEnv(os.path.join(ROOT_DIR, ENV_DIR, ".env.production")))

    # Collect static files
    if not args.skip_static and not args.git_only:
        collectstatic_cmd = f"python manage.py collectstatic --noinput"
        run_local_command(collectstatic_cmd, "Django collectstatic", ROOT_DIR)

    if not args.skip_upload and not args.git_only:
        # The base folder where you want everything to end up
        UPLOAD_DIR = "uploads"

        # List of items to copy
        # We use a tuple (source, relative_dest_subfolder)
        items_to_copy = [
            ('static', ''),  # Goes to ./upload/static
            ('.env/.env.production', '.env'),  # Goes to ./upload/.env/.env.production
            ('.env/.env.base', '.env'),  # Goes to ./upload/.env/.env.base
            ('.env/.env.blog_content', '.env'),  # Goes to ./upload/.env/.env.base
        ]

        # Remove all files in the target folder
        target_root = os.path.join(ROOT_DIR, UPLOAD_DIR)
        if os.path.exists(target_root):
            # rmtree deletes the folder and all its contents
            safe_rmtree(target_root)
            print(f"Cleared destination directory: {target_root}")

        for src, subfolder in items_to_copy:
            target_dir = os.path.join(target_root, subfolder)
            src_dir = os.path.join(ROOT_DIR, src)
            copy_and_overwrite_any(src_dir, target_dir)

        # Upload files
        ssh_upload_folder(
            host=config('EC2_HOSTNAME'),
            username=config('EC2_USER'),
            local_folder=f'{ROOT_DIR}/uploads/',
            remote_folder='/tmp/uploads/',
            key_file=dev_config('SSH_KEY_PATH'),
        )

    if not args.skip_script:
        # Run build bash script
        bash_script_name = 'prd_deploy.sh'

        if args.git_only:
            bash_script_name = 'git_pull.sh'

        host = config('EC2_HOSTNAME'),
        username = config('EC2_USER'),
        local_script_path = f'{ROOT_DIR}/tools/bash/{bash_script_name}',
        key_file = dev_config('SSH_KEY_PATH'),

        venv_path = config('VENV_PATH')
        project_root = config('PROJECT_ROOT')
        content_root = config('CONTENT_ROOT_DIR')
        script_args = f'{venv_path} {project_root} {content_root}'

        result = ssh_upload_script_execute_and_download(
            host=config('EC2_HOSTNAME'),
            username=config('EC2_USER'),
            local_script_path=f'{ROOT_DIR}/tools/bash/{bash_script_name}',
            key_file=dev_config('SSH_KEY_PATH'),
            script_args=script_args,
        )

        if result['success']:
            print(f"\n{'=' * 50}")
            print(f"✓ SUCCESS!")
            print(f"{'=' * 50}")
            print(f"Script cleaned up: {result['script_cleaned_up']}")
        else:
            print(f"\n{'=' * 50}")
            print(f"✗ FAILED!")
            print(f"{'=' * 50}")
            print(f"Error: {result['error']}")
            if 'stderr' in result:
                print(f"Error output:\n{result['stderr']}")