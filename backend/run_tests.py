import pytest
import sys

if __name__ == "__main__":
    retcode = pytest.main(["-v", "backend/tests"])
    sys.exit(retcode)
