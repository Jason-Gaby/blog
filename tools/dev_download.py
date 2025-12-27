import os
import subprocess
import shutil
from decouple import Config, RepositoryEnv

# Load environment variables
config = Config(RepositoryEnv(".env.dev"))

def run_command(command, description):
    """Runs a shell command and handles basic error reporting."""
    print(f"--- Starting: {description} ---")
    try:
        subprocess.check_call(command, shell=True)
        print(f"Successfully completed: {description}\n")
    except subprocess.CalledProcessError as e:
        print(f"Error during {description}: {e}\n")

def sync_folder(env_source_key, env_target_key):
    """Copies content from source to target defined in .env."""
    src = os.getenv(env_source_key)
    dst = os.getenv(env_target_key)

    if not src or not dst:
        print(f"Skipping {env_source_key}: Path not found in .env")
        return

    print(f"--- Syncing {env_source_key} to {env_target_key} ---")
    try:
        if os.path.exists(dst):
            shutil.rmtree(dst) # Clean target to ensure a fresh sync
        shutil.copytree(src, dst)
        print(f"Successfully synced to {dst}\n")
    except Exception as e:
        print(f"Failed to sync {src}: {e}\n")

def main():
    # 1. Git Pull
    run_command("git pull", "Git Pull (Updating Code)")

    # 2. Pip Install
    run_command("pip install -r requirements.txt", "Installing Requirements")

    # 3-6. Sync Folders
    sync_map = [
        ("SOURCE_STATIC", "TARGET_STATIC"),
        ("SOURCE_FILES", "TARGET_FILES"),
        ("SOURCE_MEDIA", "TARGET_MEDIA"),
        ("SOURCE_GRAPHS", "TARGET_GRAPHS")
    ]

    for src_key, dst_key in sync_map:
        sync_folder(src_key, dst_key)

    print("All processes completed!")

if __name__ == "__main__":
    main()