import os
import shutil
import glob
import pathlib

def clean():
    root_dir = pathlib.Path(__file__).parent.parent.resolve()
    print(f"Cleaning workspace caches in {root_dir}...")

    # 1. Remove SQLite database files
    for db_file in root_dir.rglob("*.db"):
        try:
            db_file.unlink()
            print(f"  [DELETED] Database: {db_file.relative_to(root_dir)}")
        except Exception as e:
            print(f"  [ERROR] Deleting {db_file}: {e}")

    # 2. Remove __pycache__ directories
    for pycache in root_dir.rglob("__pycache__"):
        try:
            shutil.rmtree(pycache, ignore_errors=True)
            print(f"  [DELETED] Pycache: {pycache.relative_to(root_dir)}")
        except Exception as e:
            print(f"  [ERROR] Deleting {pycache}: {e}")

    # 3. Remove .pytest_cache directories
    for pytest_cache in root_dir.rglob(".pytest_cache"):
        try:
            shutil.rmtree(pytest_cache, ignore_errors=True)
            print(f"  [DELETED] Pytest cache: {pytest_cache.relative_to(root_dir)}")
        except Exception as e:
            print(f"  [ERROR] Deleting {pytest_cache}: {e}")

    # 4. Remove Vite cache and dist output in frontend
    frontend_dir = root_dir / "frontend"
    for cache_folder in [frontend_dir / "dist", frontend_dir / "node_modules" / ".vite"]:
        if cache_folder.exists():
            try:
                shutil.rmtree(cache_folder, ignore_errors=True)
                print(f"  [DELETED] Frontend cache: {cache_folder.relative_to(root_dir)}")
            except Exception as e:
                print(f"  [ERROR] Deleting {cache_folder}: {e}")

    print("\nWorkspace clean completed successfully!")

if __name__ == "__main__":
    clean()
