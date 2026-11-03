"""Shared filesystem-identity helpers for authorization-sensitive paths (Mission 14, WP14.3).

Mission 13 showed that comparing *strings* of resolved paths gives two different security decisions
for one resource: on a case-insensitive volume ``.../Train_automation`` and ``.../train_automation``
name the same directory but compare unequal, and a symlink or alias with an innocent name looks like
a different file from the media it points at.  Every authorization decision that depends on "is this
path inside that tree?" therefore goes through this module.

What it does
------------
* :func:`canonical_path` -- expand ``~``, make absolute, resolve every existing symlink component
  (a nonexistent tail is kept as given, below its canonicalised existing parent) and fail closed
  with :class:`PathIdentityError` when that cannot be done (NUL bytes, symlink loops, I/O errors).
* :func:`is_same_location` / :func:`is_within` / :func:`relative_parts` -- compare by **filesystem
  identity** (``os.path.samefile`` on existing ancestors) rather than by spelling, so case variants,
  Unicode-normalisation variants and macOS firmlink spellings of one directory agree.  When the
  reference tree does not exist (a synthetic root that was never created) the comparison falls back
  to a case- and Unicode-folded string comparison, which can only over-match (fail closed).
* :func:`resolve_untrusted_relative` -- turn an *untrusted* relative path (for example a URL path)
  into a file inside an allowlisted root.  Repeated percent-decoding, backslash separators, NUL and
  control characters, absolute paths and ``..`` are refused; the result is canonicalised and must
  stay inside the root *after* symlink resolution.

What it does not do
-------------------
It makes no claim of OS-level isolation.  Hard links to a protected file, bind mounts created after
the check, and a file replaced between check and use are outside its reach (the usual
time-of-check / time-of-use limit of any user-space path check).
"""

from __future__ import annotations

import os
import unicodedata
import urllib.parse
from collections.abc import Iterable, Sequence
from pathlib import Path


class PathIdentityError(ValueError):
    """A path could not be canonicalised or an untrusted path was refused."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"[{code}] {detail}")


def canonical_path(path: Path | str) -> Path:
    """Absolute path with every existing symlink resolved; fail closed on any doubt."""
    try:
        text = os.fspath(path)
    except TypeError as exc:
        raise PathIdentityError("PATH_INVALID", "path is not path-like") from exc
    if not isinstance(text, str):
        raise PathIdentityError("PATH_INVALID", "bytes paths are not accepted")
    if "\x00" in text:
        raise PathIdentityError("PATH_INVALID", "path contains a NUL byte")
    if not text.strip():
        raise PathIdentityError("PATH_INVALID", "path is empty")
    try:
        candidate = Path(text).expanduser()
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        return candidate.resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as exc:  # symlink loops raise RuntimeError
        raise PathIdentityError(
            "PATH_UNRESOLVABLE", f"path could not be canonicalised ({type(exc).__name__})"
        ) from exc


def _fold(text: str) -> str:
    return unicodedata.normalize("NFC", text).casefold()


def _folded_parts(path: Path) -> tuple[str, ...]:
    return tuple(_fold(part) for part in path.parts)


def _samefile(left: Path, right: Path) -> bool | None:
    """True/False when both exist; None when identity cannot be established."""
    try:
        return os.path.samefile(left, right)
    except (FileNotFoundError, NotADirectoryError):
        return None
    except OSError:
        return None


def _matching_ancestor(path: Path, root: Path) -> Path | None:
    """The ancestor-or-self of ``path`` that is the same filesystem object as ``root``."""
    if path == root:
        return path
    if root in path.parents:
        return root
    root_exists = root.exists()
    if root_exists:
        # Every ancestor is tried: an alias (case variant, firmlink spelling) may differ from the
        # reference in depth as well as in spelling.  Each probe is one ``stat``; paths are shallow.
        for ancestor in (path, *path.parents):
            if _samefile(ancestor, root):
                return ancestor
        return None
    # Reference tree absent: compare folded spellings (over-matches, never under-matches).
    folded_root = _folded_parts(root)
    folded_path = _folded_parts(path)
    if folded_path[: len(folded_root)] == folded_root:
        return Path(*path.parts[: len(root.parts)])
    return None


def is_same_location(left: Path | str, right: Path | str) -> bool:
    """True when both paths name the same filesystem location (or cannot be told apart)."""
    a, b = canonical_path(left), canonical_path(right)
    if a == b:
        return True
    same = _samefile(a, b)
    if same is not None:
        return same
    return _folded_parts(a) == _folded_parts(b)


def is_within(path: Path | str, root: Path | str, *, include_root: bool = True) -> bool:
    """True when ``path`` is ``root`` or lies below it, judged by filesystem identity."""
    target, tree = canonical_path(path), canonical_path(root)
    ancestor = _matching_ancestor(target, tree)
    if ancestor is None:
        return False
    return include_root or ancestor != target


def is_within_any(
    path: Path | str, roots: Iterable[Path | str], *, include_root: bool = True
) -> bool:
    target = canonical_path(path)
    return any(is_within(target, root, include_root=include_root) for root in roots)


def relative_parts(path: Path | str, root: Path | str) -> tuple[str, ...] | None:
    """Path components of ``path`` below ``root`` (as spelled), or None when outside."""
    target, tree = canonical_path(path), canonical_path(root)
    ancestor = _matching_ancestor(target, tree)
    if ancestor is None:
        return None
    return tuple(target.parts[len(ancestor.parts) :])


def _decode_fully(text: str, *, max_rounds: int = 4) -> str:
    """Percent-decode until stable; refuse an input that keeps changing (deep encoding)."""
    current = text
    for _ in range(max_rounds):
        decoded = urllib.parse.unquote(current)
        if decoded == current:
            return current
        current = decoded
    raise PathIdentityError("PATH_OVER_ENCODED", "path is encoded more times than is plausible")


def resolve_untrusted_relative(
    root: Path | str,
    untrusted: str,
    *,
    allowed_suffixes: Sequence[str] | None = None,
    must_exist: bool = True,
) -> Path:
    """Map an untrusted relative path onto a regular file inside ``root`` or raise.

    The returned path is canonical (symlinks resolved) and verified to lie inside ``root`` by
    filesystem identity, so a symlink that points out of ``root`` and a case-variant spelling of a
    directory outside ``root`` are both refused.
    """
    if not isinstance(untrusted, str):
        raise PathIdentityError("PATH_INVALID", "path must be text")
    decoded = _decode_fully(untrusted)
    if "\x00" in decoded or any(ord(ch) < 32 or ord(ch) == 127 for ch in decoded):
        raise PathIdentityError("PATH_INVALID", "path contains control characters")
    if "\\" in decoded:
        raise PathIdentityError("PATH_INVALID", "backslash separators are not accepted")
    if decoded.startswith(("/", "~")) or (len(decoded) > 1 and decoded[1] == ":"):
        raise PathIdentityError("PATH_ABSOLUTE", "absolute paths are not accepted")
    parts = [part for part in decoded.split("/") if part not in ("", ".")]
    if not parts:
        raise PathIdentityError("PATH_INVALID", "path is empty")
    if any(part == ".." or part.strip(". ") == "" for part in parts):
        raise PathIdentityError("PATH_TRAVERSAL", "parent-directory components are not accepted")
    tree = canonical_path(root)
    candidate = canonical_path(tree.joinpath(*parts))
    if not is_within(candidate, tree, include_root=False):
        raise PathIdentityError("PATH_OUTSIDE_ROOT", "path resolves outside the permitted root")
    if allowed_suffixes is not None and candidate.suffix.lower() not in {
        suffix.lower() for suffix in allowed_suffixes
    }:
        raise PathIdentityError("PATH_TYPE_NOT_ALLOWED", "file type is not served")
    if must_exist and not candidate.is_file():
        raise PathIdentityError("PATH_NOT_FOUND", "no such file")
    return candidate


__all__ = [
    "PathIdentityError",
    "canonical_path",
    "is_same_location",
    "is_within",
    "is_within_any",
    "relative_parts",
    "resolve_untrusted_relative",
]
