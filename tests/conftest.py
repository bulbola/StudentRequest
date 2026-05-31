from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
import pytest
from run import app as flask_app


@pytest.fixture
def client():
    flask_app.config.update(TESTING=True)

    with flask_app.test_client() as test_client:
        yield test_client