import pytest
import sys
import os

if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root_dir)
    sys.path.insert(0, os.path.join(root_dir, "backend"))
    
    print("Executing pytest on backend/tests...")
    code = pytest.main(["-v", "backend/tests"])
    print(f"Pytest finish exit code: {code}")
    sys.exit(code)
