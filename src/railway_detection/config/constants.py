"""Lightweight configuration constants with zero heavy runtime imports."""

from __future__ import annotations

from pathlib import Path

DEFAULT_EXPERIMENT_REGISTRY = Path("results/experiment_registry.jsonl")
EXPERIMENT_REGISTRY_ENV = "RAILWAY_EXPERIMENT_REGISTRY"

__all__ = [
    "DEFAULT_EXPERIMENT_REGISTRY",
    "EXPERIMENT_REGISTRY_ENV",
]
