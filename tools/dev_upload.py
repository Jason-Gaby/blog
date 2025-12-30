import os
import subprocess
import shutil
from decouple import Config, RepositoryEnv

from definitions import ENV_DIR

# Load environment variables
config = Config(RepositoryEnv(os.path.join(ENV_DIR, ".env.dev")))


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


def upload_folder(local_dir, remote_dir):
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
    run_command("git push", "Pushing to Remote Repository")

    remote_dir = config("REMOTE_DIR")
    local_dir = config("LOCAL_DIR")

    # 2. Upload Folders (Target -> Source)
    sync_map = [
        (config("LOCAL_STATIC"), config("REMOTE_STATIC")),
        (config("LOCAL_MEDIA"), config("REMOTE_MEDIA")),
    ]

    for local_key, remote_key in sync_map:
        local_path = os.path.join(local_dir, local_key)
        remote_path = os.path.join(remote_dir, remote_key)
        upload_folder(local_path, remote_path)

    print("--- Process Finished Successfully ---")


if __name__ == "__main__":
    main()