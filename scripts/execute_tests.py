import pytest
import sys
import os

def run():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root_dir)
    sys.path.insert(0, os.path.join(root_dir, "backend"))
    
    print(f"[TEST RUNNER] Running all backend automated unit & E2E tests in {root_dir}/backend/tests...")
    exit_code = pytest.main(["-v", "backend/tests"])
    if exit_code == 0:
        print("\n[SUCCESS] ALL TEST SUITES PASSED CLEANLY!")
    else:
        print(f"\n[FAILURE] pytest exited with code {exit_code}")
    return exit_code

if __name__ == "__main__":
    sys.exit(run())
