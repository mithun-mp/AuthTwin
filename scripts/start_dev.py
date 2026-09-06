import os
import sys
import subprocess
import time
import pathlib
import shutil

def clean_cache(root_dir):
    print("[CLEAN] Purging database, pycache, and frontend build caches...")
    
    # 1. Remove SQLite database files
    for db_file in pathlib.Path(root_dir).rglob("*.db"):
        try:
            db_file.unlink()
            print(f"  - Deleted database: {db_file.name}")
        except Exception as e:
            print(f"  - Warning deleting {db_file.name}: {e}")

    # 2. Remove __pycache__ directories
    for pycache in pathlib.Path(root_dir).rglob("__pycache__"):
        try:
            shutil.rmtree(pycache, ignore_errors=True)
        except Exception:
            pass

    # 3. Remove .pytest_cache directories
    for pytest_cache in pathlib.Path(root_dir).rglob(".pytest_cache"):
        try:
            shutil.rmtree(pytest_cache, ignore_errors=True)
        except Exception:
            pass

    # 4. Remove Vite cache and dist in frontend
    frontend_dir = os.path.join(root_dir, "frontend")
    for cache_folder in [os.path.join(frontend_dir, "dist"), os.path.join(frontend_dir, "node_modules", ".vite")]:
        if os.path.exists(cache_folder):
            try:
                shutil.rmtree(cache_folder, ignore_errors=True)
                print(f"  - Deleted frontend cache folder: {os.path.basename(cache_folder)}")
            except Exception as e:
                print(f"  - Warning deleting {cache_folder}: {e}")

def main():
    print("=" * 60)
    print("AUTHTWIN WORKSTATION — FRESH CLEAN, REBUILD & STARTUP")
    print("=" * 60)

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root_dir)

    # 1. Clean Caches
    clean_cache(root_dir)

    frontend_dir = os.path.join(root_dir, "frontend")
    tailwind_pkg = os.path.join(frontend_dir, "node_modules", "tailwindcss")

    # 2. Check & auto-install frontend dependencies
    if not os.path.exists(tailwind_pkg):
        print("[SETUP] Installing frontend node_modules (including Tailwind CSS)...")
        try:
            subprocess.run("npm install", shell=True, cwd=frontend_dir, check=True)
            print("[SETUP] Frontend dependencies installed successfully!")
        except Exception as e:
            print(f"[WARNING] Failed to run npm install automatically: {e}")

    # 3. Fresh Rebuild Frontend
    print("[BUILD] Rebuilding Frontend Dashboard bundle (npm run build)...")
    try:
        subprocess.run("npm run build", shell=True, cwd=frontend_dir, check=True)
        print("[BUILD] Frontend bundle freshly rebuilt!")
    except Exception as e:
        print(f"[WARNING] npm run build note: {e}")

    # 4. Execute Pytest Suite (Unit & E2E Tests)
    print("[TESTS] Executing Pytest backend unit & E2E test suites...")
    try:
        import pytest
        sys.path.insert(0, os.path.join(root_dir, "backend"))
        ret = pytest.main(["-v", os.path.join(root_dir, "backend", "tests")])
        if ret == 0:
            print("[TESTS] All Backend Unit & E2E Tests PASSED SUCCESSFULLY!")
        else:
            print(f"[WARNING] Pytest suite returned code {ret}")
    except Exception as e:
        print(f"[WARNING] Could not run pytest automatically: {e}")

    sys.path.insert(0, os.path.join(root_dir, "backend"))
    from app.config import settings

    backend_host = settings.AUTHTWIN_API_HOST
    backend_port = str(settings.AUTHTWIN_API_PORT)
    ref_host = os.getenv("REFERENCE_TARGET_HOST", "127.0.0.1")
    ref_port = os.getenv("REFERENCE_TARGET_PORT", "8001")
    frontend_port = str(settings.AUTHTWIN_FRONTEND_PORT)

    child_env = os.environ.copy()
    child_env["VITE_AUTHTWIN_API_URL"] = f"http://{backend_host}:{backend_port}"
    child_env["AUTHTWIN_API_PORT"] = backend_port
    child_env["AUTHTWIN_FRONTEND_PORT"] = frontend_port
    child_env["REFERENCE_TARGET_HOST"] = ref_host
    child_env["REFERENCE_TARGET_PORT"] = ref_port

    print(f"\n[1/3] Launching AuthTwin Backend (http://{backend_host}:{backend_port})...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", backend_host, "--port", backend_port, "--reload"],
        cwd=os.path.join(root_dir, "backend"),
        env=child_env
    )

    print(f"[2/3] Launching Reference Target API (http://{ref_host}:{ref_port})...")
    ref_proc = subprocess.Popen(
        [sys.executable, "target/reference-api/app.py"],
        cwd=root_dir,
        env=child_env
    )

    print(f"[3/3] Launching Frontend Dashboard (http://localhost:{frontend_port})...")
    frontend_proc = subprocess.Popen(
        "npm run dev",
        shell=True,
        cwd=frontend_dir,
        env=child_env
    )

    print("\n[SUCCESS] AuthTwin Services Freshly Built & Started!")
    print(f" - Backend API:  http://{backend_host}:{backend_port} (Swagger: http://{backend_host}:{backend_port}/docs)")
    print(f" - Frontend UI:   http://localhost:{frontend_port}")
    print(f" - Target API:   http://{ref_host}:{ref_port}")
    print("\nPress Ctrl+C to stop all services.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down AuthTwin processes...")
        backend_proc.terminate()
        ref_proc.terminate()
        frontend_proc.terminate()
        print("Done.")

if __name__ == "__main__":
    main()

