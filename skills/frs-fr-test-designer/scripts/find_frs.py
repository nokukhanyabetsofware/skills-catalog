from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

SKIP_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "node_modules", "dist", "build", "target", "__pycache__", "skills"}
DOC_EXTS = {".md", ".txt", ".rst"}
HINTS = [
    ("name:frs", re.compile(r"frs|functional[-_ ]requirements", re.I)),
    ("content:fr", re.compile(r"\bFR-\d+(?:\.\d+)?\b")),
    ("content:ac", re.compile(r"\bAC-[A-Z0-9-]+\b")),
    ("content:acceptance", re.compile(r"Acceptance criteria", re.I)),
    ("content:applicability", re.compile(r"Applicability:", re.I)),
    ("content:bdd", re.compile(r"^\s*(Given|When|Then)\b", re.M)),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Locate likely FRS files.")
    parser.add_argument("--root", default=".", help="Repository root to search.")
    return parser.parse_args()


def iter_docs(root: Path):
    for current, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        base = Path(current)
        for name in files:
            path = base / name
            if path.suffix.lower() in DOC_EXTS:
                yield path


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return ""


def score_name(path: Path) -> list[str]:
    return ["name:frs"] if HINTS[0][1].search(path.name) else []


def score_text(text: str) -> list[str]:
    return [label for label, pattern in HINTS[1:] if pattern.search(text)]


def build_candidate(root: Path, path: Path):
    text = read_text(path)
    reasons = score_name(path) + score_text(text)
    if not text.strip() or not reasons:
        return None
    score = len(reasons) + (2 if path.name.lower() == "frs.md" else 0)
    rel_path = path.relative_to(root).as_posix()
    return {"path": rel_path, "score": score, "size": path.stat().st_size, "reasons": reasons}


def main() -> None:
    root = Path(parse_args().root).resolve()
    candidates = [item for path in iter_docs(root) if (item := build_candidate(root, path))]
    ordered = sorted(candidates, key=lambda item: (-item["score"], -item["size"], item["path"]))
    print(json.dumps({"root": str(root), "candidates": ordered}, indent=2))


if __name__ == "__main__":
    main()
