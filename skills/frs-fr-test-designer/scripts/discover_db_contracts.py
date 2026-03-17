from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

SKIP_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "node_modules", "dist", "build", "target", "__pycache__", "skills"}
CODE_EXTS = {".cs", ".go", ".java", ".js", ".kt", ".py", ".sql", ".ts"}
PROC_PATTERNS = [
    re.compile(r"\bEXEC(?:UTE)?\s+([\[\]\w]+\.[\[\]\w]+|\w+)", re.I),
    re.compile(r"\bStoredProcedure\s*[:=]\s*['\"]([\[\]\w]+\.[\[\]\w]+|\w+)['\"]", re.I),
    re.compile(r"\bCommandText\s*=\s*['\"]([\[\]\w]+\.[\[\]\w]+|\w+)['\"]", re.I),
    re.compile(r"\b(?:FromSql|ExecuteSql|SqlQuery)\w*\(\s*\$?['\"].*?EXEC(?:UTE)?\s+([\[\]\w]+\.[\[\]\w]+|\w+)", re.I | re.S),
]
PARAM_PATTERNS = [
    re.compile(r"@([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"\b(?:Add|AddWithValue|SqlParameter)\(\s*['\"]@?([A-Za-z_][A-Za-z0-9_]*)['\"]"),
    re.compile(r"\bParameterName\s*=\s*['\"]@?([A-Za-z_][A-Za-z0-9_]*)['\"]"),
]
OUTPUT_PATTERNS = [
    re.compile(r"\[['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\]"),
    re.compile(r"\bGetOrdinal\(\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*\)"),
    re.compile(r"\bAS\s+([A-Za-z_][A-Za-z0-9_]*)", re.I),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover likely DB contracts from repo code.")
    parser.add_argument("--root", default=".", help="Repository root to search.")
    parser.add_argument("--query", default="", help="Optional keywords to narrow results.")
    return parser.parse_args()


def query_tokens(value: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", value.lower()) if len(token) > 2]


def iter_code_files(root: Path):
    for current, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        base = Path(current)
        for name in files:
            path = base / name
            if path.suffix.lower() in CODE_EXTS:
                yield path


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return ""


def include_file(path: Path, text: str, tokens: list[str]) -> bool:
    haystack = f"{path.as_posix()} {text[:6000]}".lower()
    return True if not tokens else any(token in haystack for token in tokens)


def procedures(text: str) -> list[str]:
    found = []
    for pattern in PROC_PATTERNS:
        found.extend(pattern.findall(text))
    return sorted(set(name.strip("[]") for name in found if name))


def parameters(text: str) -> list[str]:
    found = []
    for pattern in PARAM_PATTERNS:
        found.extend(pattern.findall(text))
    return sorted(set(found))


def outputs(text: str) -> list[str]:
    found = []
    for pattern in OUTPUT_PATTERNS:
        found.extend(pattern.findall(text))
    return sorted(set(found))


def infer_operation(name: str) -> str:
    lowered = name.lower()
    if any(token in lowered for token in ("create", "insert", "add")):
        return "create"
    if "update" in lowered and "status" in lowered:
        return "update_status"
    if "update" in lowered:
        return "update"
    if any(token in lowered for token in ("list", "search", "findall")):
        return "list"
    if any(token in lowered for token in ("audit", "history", "log")):
        return "audit"
    if any(token in lowered for token in ("get", "read", "find")):
        return "get"
    return "unknown"


def build_contracts(root: Path, path: Path, text: str) -> list[dict]:
    rel_path = path.relative_to(root).as_posix()
    params = parameters(text)
    cols = outputs(text)
    return [contract_dict(name, rel_path, params, cols) for name in procedures(text)]


def contract_dict(name: str, rel_path: str, params: list[str], cols: list[str]) -> dict:
    return {
        "procedure": name,
        "operation": infer_operation(name),
        "input_parameters": params,
        "output_columns": cols,
        "contract_source": "repo",
        "source_paths": [rel_path],
    }


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    tokens = query_tokens(args.query)
    contracts = []
    for path in iter_code_files(root):
        text = read_text(path)
        if text and include_file(path, text, tokens):
            contracts.extend(build_contracts(root, path, text))
    ordered = sorted(contracts, key=lambda item: (item["procedure"], item["source_paths"][0]))
    print(json.dumps({"root": str(root), "query": args.query, "contracts": ordered}, indent=2))


if __name__ == "__main__":
    main()
