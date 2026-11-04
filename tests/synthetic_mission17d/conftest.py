"""Constructed metadata only; isolate from root conftest and production CLI.

Run with --confcutdir=tests/synthetic_mission17d, plugin autoload disabled and
cache/bytecode writes disabled. The IO guard below is test isolation, not a
production sandbox or authorization mechanism.
"""

import builtins
import io
import os
import socket
import subprocess
from pathlib import Path

import pytest

from railway_detection.synthetic.grouped_cv import (
    Annotation,
    Asset,
    Capture,
    DatasetRole,
    MetadataValue,
    PhysicalEvent,
    SyntheticDataset,
)


@pytest.fixture(autouse=True)
def no_component_io(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("synthetic component attempted file/network/process IO")
    for owner, name in [(builtins, "open"), (io, "open"), (os, "open"),
                        (Path, "open"), (Path, "read_bytes"), (Path, "read_text"),
                        (Path, "write_bytes"), (Path, "write_text"),
                        (socket, "socket"), (socket, "create_connection"),
                        (subprocess, "Popen")]:
        monkeypatch.setattr(owner, name, denied)


@pytest.fixture
def dataset_factory():
    def build(labels=(('front',),)*6, *, roles=None, counts=None):
        roles = roles or (DatasetRole.DEVELOPMENT_POOL,)*len(labels)
        counts = counts or (1,)*len(labels)
        events, captures, assets, annotations = [], [], [], []
        known = lambda v: MetadataValue(v, None, "synthetic:metadata:constructed")
        for i, (event_labels, role, count) in enumerate(zip(labels, roles, counts, strict=True)):
            event_id, capture_id = f"synthetic:event:{i:04}", f"synthetic:capture:{i:04}"
            events.append(PhysicalEvent(event_id, role, tuple(event_labels),
                                        weather=known("constructed-dry")))
            captures.append(Capture(capture_id, (event_id,), camera=known("camera-a"),
                                    crossing=known("constructed-crossing")))
            for j in range(count):
                asset_id = f"synthetic:asset:{i:04}:{j:04}"
                annotation_id = f"synthetic:annotation:{i:04}:{j:04}"
                assets.append(Asset(asset_id, event_id, "STILL", (annotation_id,), capture_id))
                annotations.append(Annotation(annotation_id, asset_id, tuple(event_labels),
                                              confirmed_empty=not event_labels))
        return SyntheticDataset("synthetic:dataset:constructed", tuple(events), tuple(captures),
                                tuple(assets), tuple(annotations))
    return build
