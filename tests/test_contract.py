import json
import pathlib

from app.main import app

CONTRACT = pathlib.Path(__file__).resolve().parent.parent / "openapi.json"


def test_published_contract_matches_running_app():
    """openapi.json in the repo must be exactly what the app serves. Regenerate with
    `python -m scripts.export_openapi` after changing any route or schema."""
    committed = json.loads(CONTRACT.read_text())
    assert committed == json.loads(json.dumps(app.openapi()))
