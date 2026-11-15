"""Pure-stdlib AST and module-load isolation audit for synthetic test suites.

Avoids spawning subprocesses so ``SYNTHETIC_ONLY`` suites keep static/runtime
coverage under ``scripts/classify_test_access.py`` while remaining immune to
pytest collection order when production tests run in the same session.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPO_ROOT / "src"
TESTS_ROOT = REPO_ROOT / "tests"


def _module_to_path(module_name: str) -> Path | None:
    parts = module_name.split(".")
    if not parts:
        return None
    base_root = TESTS_ROOT.parent if parts[0] == "tests" else SRC_ROOT
    rel = Path(*parts)
    py_path = base_root / f"{rel}.py"
    if py_path.is_file():
        return py_path
    init_path = base_root / rel / "__init__.py"
    if init_path.is_file():
        return init_path
    return None


def _resolve_relative_import(current_module: str, is_pkg: bool, level: int, target: str | None) -> str:
    parts = current_module.split(".")
    pkg_parts = parts if is_pkg else parts[:-1]
    trim = level - 1
    anchor = pkg_parts[: len(pkg_parts) - trim] if trim else pkg_parts
    return ".".join([*anchor, target] if target else anchor)


def extract_direct_imports(path: Path, current_module: str) -> set[str]:
    """Return every dotted module name referenced anywhere inside ``path``'s AST."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    is_pkg = path.name == "__init__.py"
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            base = (
                _resolve_relative_import(current_module, is_pkg, node.level, node.module)
                if node.level > 0
                else (node.module or "")
            )
            if base:
                imports.add(base)
                for alias in node.names:
                    if alias.name != "*":
                        candidate = f"{base}.{alias.name}"
                        if _module_to_path(candidate) is not None:
                            imports.add(candidate)
    return imports


def collect_transitive_imports(entry_modules: tuple[str, ...]) -> tuple[dict[str, set[str]], set[str]]:
    """Compute AST transitive import closure across local modules under ``src/`` and ``tests/``."""
    queue = list(entry_modules)
    visited: dict[str, set[str]] = {}
    all_imports: set[str] = set()
    while queue:
        mod = queue.pop(0)
        if mod in visited:
            continue
        mod_path = _module_to_path(mod)
        if mod_path is None:
            continue
        direct = extract_direct_imports(mod_path, mod)
        visited[mod] = direct
        all_imports.update(direct)
        for dep in sorted(direct):
            parts = dep.split(".")
            for i in range(1, len(parts) + 1):
                prefix = ".".join(parts[:i])
                if prefix not in visited and _module_to_path(prefix) is not None:
                    queue.append(prefix)
    return visited, all_imports


def matches_forbidden(module_name: str, forbidden: tuple[str, ...]) -> bool:
    """Return True when ``module_name`` equals or falls under a forbidden prefix."""
    return any(module_name == bad or module_name.startswith(f"{bad}.") for bad in forbidden)


def capture_loaded_forbidden(forbidden: tuple[str, ...]) -> set[str]:
    """Snapshot forbidden modules already present before synthetic imports execute."""
    return {name for name in sys.modules if matches_forbidden(name, forbidden)}


def assert_snapshot_isolated(
    *,
    visited_modules: dict[str, set[str]],
    all_imports: set[str],
    forbidden: tuple[str, ...],
    runtime_leaks: set[str],
) -> None:
    """Assert zero forbidden imports in an import-time AST snapshot and import delta."""
    assert visited_modules, "Expected non-empty transitive module AST inspection"
    static_leaks = sorted(mod for mod in all_imports if matches_forbidden(mod, forbidden))
    assert not static_leaks, f"Forbidden imports in transitive AST closure: {static_leaks}"
    assert not runtime_leaks, f"Synthetic imports loaded forbidden modules at runtime: {sorted(runtime_leaks)}"


def check_pure_verifier_ast(
    module_path: Path,
    *,
    forbidden_def_prefixes: tuple[str, ...],
    forbidden_call_names: tuple[str, ...],
) -> list[str]:
    """Return AST-defined function names while verifying zero IO/fit/load AST patterns."""
    tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
    defs: list[str] = []
    bad_defs: list[str] = []
    bad_calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defs.append(node.name)
            if node.name.startswith(forbidden_def_prefixes):
                bad_defs.append(node.name)
        elif isinstance(node, ast.Call):
            fn = node.func
            name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else ""
            if name in forbidden_call_names:
                bad_calls.append(name)
    assert not bad_defs, f"Forbidden fit/load/IO functions in {module_path}: {bad_defs}"
    assert not bad_calls, f"Forbidden IO/runtime calls in {module_path}: {bad_calls}"
    return defs
