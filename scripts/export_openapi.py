"""Write the published contract to openapi.json. Usage: python -m scripts.export_openapi"""
import json
import os
import pathlib

# The app needs these to import; the values are not used to generate the contract.
os.environ.setdefault("DATABASE_URL", "postgresql://unused")
os.environ.setdefault("JWT_SECRET", "unused")

from app.main import app  # noqa: E402

path = pathlib.Path(__file__).resolve().parent.parent / "openapi.json"
path.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n")
print(f"Wrote {path}")
