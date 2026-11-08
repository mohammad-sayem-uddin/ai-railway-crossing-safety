"""Collection evidence for the resource-free runner; no production fixtures or overrides."""

import json
import os
from pathlib import Path


def pytest_collection_finish(session):
    output = os.environ.get("MISSION23_COLLECTION_OUTPUT")
    if output:
        Path(output).write_text(json.dumps([item.nodeid for item in session.items], indent=2))
