import os
import subprocess
import shutil
from decouple import Config, RepositoryEnv

# Load environment variables
config = Config(RepositoryEnv(".env.dev"))


def run_command(command, description):
    """Runs a shell command and handles errors."""
    print(f"--- Starting: {description} ---")
    try:
        subprocess.check_call(command, shell=True)
        print(f"Successfully completed: {description}\n")
    except subprocess.CalledProcessError as e:
        print(f"Error during {description}: {e}")
        # We stop the script if Git fails to avoid versioning mismatches
        exit(1)


def upload_folder(local_path_key, remote_path_key):
    """Copies content from local target to remote source."""
    local_dir = os.getenv(local_path_key)
    remote_dir = os.getenv(remote_path_key)

    if not local_dir or not remote_dir:
        print(f"Skipping: Keys {local_path_key} or {remote_path_key} not in .env")
        return

    print(f"--- Uploading {local_dir} -> {remote_dir} ---")
    try:
        if not os.path.exists(local_dir):
            print(f"Warning: Local directory {local_dir} does not exist. Skipping.")
            return

        # Clean the destination to ensure it matches the local state exactly
        if os.path.exists(remote_dir):
            shutil.rmtree(remote_dir)

        shutil.copytree(local_dir, remote_dir)
        print(f"Successfully uploaded to {remote_dir}\n")
    except Exception as e:
        print(f"Failed to upload {local_dir}: {e}\n")


def main():
    # 1. Git Push Process
    # We use 'git add .' and 'git commit' as well, otherwise push might have nothing to do
    commit_msg = input("Enter commit message (or press Enter for 'auto-upload'): ") or "auto-upload"

    run_command("git add .", "Staging changes")
    run_command(f'git commit -m "{commit_msg}"', "Committing changes")
    run_command("git push", "Pushing to Remote Repository")

    # 2. Upload Folders (Target -> Source)
    sync_map = [
        (config("TARGET_STATIC"), config("SOURCE_STATIC")),
        (config("TARGET_FILES"), config("SOURCE_FILES")),
        (config("TARGET_MEDIA"), config("SOURCE_MEDIA")),
        (config("TARGET_GRAPHS"), config("SOURCE_GRAPHS"))
    ]

    for local_key, remote_key in sync_map:
        upload_folder(local_key, remote_key)

    print("--- Process Finished Successfully ---")


if __name__ == "__main__":
    main()