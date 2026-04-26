import json
from pathlib import Path
import pytest

@pytest.fixture
def sample_client_dict():
    p = Path(__file__).resolve().parents[1] / "data" / "fictional_client.json"
    return json.loads(p.read_text(encoding="utf-8"))
