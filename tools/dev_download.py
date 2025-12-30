import os
import subprocess
import shutil
import stat
from decouple import Config, RepositoryEnv, Csv

from definitions import ENV_DIR

# Load environment variables
config = Config(RepositoryEnv(os.path.join(ENV_DIR, ".env.dev")))

def remove_readonly(func, path, _):
    """Clear the readonly bit and reattempt the removal."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def run_command(command, description):
    """Runs a shell command and handles basic error reporting."""
    print(f"--- Starting: {description} ---")
    try:
        subprocess.check_call(command, shell=True)
        print(f"Successfully completed: {description}\n")
    except subprocess.CalledProcessError as e:
        print(f"Error during {description}: {e}\n")

def sync_folder(local_dir, remote_dir):
    """Copies content from source to target defined in .env."""
    print(f"--- Syncing {remote_dir} to {local_dir} ---")
    try:
        if os.path.exists(local_dir):
            shutil.rmtree(local_dir, onerror=remove_readonly) # Clean target to ensure a fresh sync
        shutil.copytree(remote_dir, local_dir)
        print(f"Successfully synced to {local_dir}\n")
    except Exception as e:
        print(f"Failed to sync {remote_dir}: {e}\n")

def main():
    # 1. Git Pull
    run_command("git pull", "Git Pull (Updating Code)")

    # 2. Pip Install
    run_command("pip install -r requirements.txt", "Installing Requirements")

    # 3. Sync Folders
    remote_dir = config("REMOTE_DIR")
    local_dir = config("LOCAL_DIR")

    # 4. Upload Folders (Target -> Source)
    sync_map = [
        (config("LOCAL_STATIC"), config("REMOTE_STATIC")),
        (config("LOCAL_MEDIA"), config("REMOTE_MEDIA")),
    ]

    for local_key, remote_key in sync_map:
        local_path = os.path.join(local_dir, local_key)
        remote_path = os.path.join(remote_dir, remote_key)
        sync_folder(local_path, remote_path)

    # 5. Sync special folders
    sync_folders = config('SYNC_FOLDERS', cast=Csv())
    for folder in sync_folders:
        source_path = os.path.join(local_dir, config('LOCAL_STATIC'), folder)
        target_path = os.path.join(local_dir, config('SYNC_ROOT_DIR'), folder)
        sync_folder(target_path, source_path)

    print("All processes completed!")

if __name__ == "__main__":
    main()