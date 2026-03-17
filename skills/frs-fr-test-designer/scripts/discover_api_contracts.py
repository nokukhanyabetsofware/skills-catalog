from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

SKIP_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "node_modules", "dist", "build", "target", "__pycache__", "skills"}
CODE_EXTS = {".cs", ".go", ".java", ".js", ".jsx", ".kt", ".py", ".ts", ".tsx"}
TYPE_RE = re.compile(r"(?:class|interface|type|record)\s+(?P<name>\w+)\b[^{=]*[{=](?P<body>.*?)[};]", re.S)
FIELD_RES = [
    re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\??\s*:", re.M),
    re.compile(r"^\s*(?:public|private|protected|internal)\s+\S+(?:\s+\S+)?\s+([A-Za-z_][A-Za-z0-9_]*)\s*[{;=]", re.M),
]
ROUTE_PATTERNS = [
    (re.compile(r"@(Get|Post|Put|Delete|Patch)\(\s*['\"]([^'\"]+)['\"]", re.I), False),
    (re.compile(r"\[(HttpGet|HttpPost|HttpPut|HttpDelete|HttpPatch)\(\s*['\"]([^'\"]*)['\"]?\s*\)\]", re.I), False),
    (re.compile(r"\b(?:router|app)\.(get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]", re.I), False),
    (re.compile(r"\bMap(Get|Post|Put|Delete|Patch)\(\s*['\"]([^'\"]+)['\"]", re.I), False),
    (re.compile(r"\baxios\.(get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]", re.I), False),
    (re.compile(r"\bmethod\s*:\s*['\"](GET|POST|PUT|DELETE|PATCH)['\"].*?\b(?:path|url)\b\s*:\s*['\"]([^'\"]+)['\"]", re.I | re.S), False),
    (re.compile(r"\bfetch\(\s*['\"]([^'\"]+)['\"].*?\bmethod\s*:\s*['\"](GET|POST|PUT|DELETE|PATCH)['\"]", re.I | re.S), True),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover likely API contracts from repo code.")
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


def normalize_method(raw: str) -> str:
    return raw.replace("Http", "").upper()


def route_hits(text: str) -> list[tuple[str, str]]:
    hits = []
    for pattern, flipped in ROUTE_PATTERNS:
        for match in pattern.findall(text):
            method, path = (match[1], match[0]) if flipped else (match[0], match[1])
            hits.append((normalize_method(method), path or "/"))
    return sorted(set(hits))


def fields_from_blocks(text: str, suffixes: tuple[str, ...]) -> list[str]:
    names = []
    for match in TYPE_RE.finditer(text):
        if match.group("name").lower().endswith(suffixes):
            names.extend(fields_from_body(match.group("body")))
    return dedupe(names)


def fields_from_body(body: str) -> list[str]:
    names = []
    for pattern in FIELD_RES:
        names.extend(pattern.findall(body))
    return names


def marker_fields(text: str, markers: tuple[str, ...]) -> list[str]:
    lines = [line for line in text.splitlines() if any(marker in line.lower() for marker in markers)]
    joined = "\n".join(lines[:40])
    return dedupe(re.findall(r"['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*:", joined))


def dedupe(values: list[str]) -> list[str]:
    return sorted({value for value in values if value})


def operation_name(method: str, path: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", f"{method}_{path}".lower()).strip("_")
    return slug or method.lower()


def build_contracts(root: Path, path: Path, text: str) -> list[dict]:
    routes = route_hits(text)
    request_fields = fields_from_blocks(text, ("request", "input", "payload", "dto")) or marker_fields(text, ("request", "body", "payload"))
    success_fields = fields_from_blocks(text, ("response", "result", "output", "dto")) or marker_fields(text, ("response", "result", "output"))
    error_fields = fields_from_blocks(text, ("error", "failure", "problem")) or marker_fields(text, ("error", "problem", "failure"))
    rel_path = path.relative_to(root).as_posix()
    return [contract_dict(method, route, rel_path, request_fields, success_fields, error_fields) for method, route in routes]


def contract_dict(method: str, path: str, rel_path: str, request_fields: list[str], success_fields: list[str], error_fields: list[str]) -> dict:
    return {
        "operation_name": operation_name(method, path),
        "method": method,
        "path": path,
        "request_fields": request_fields,
        "response_success_fields": success_fields,
        "response_error_fields": error_fields,
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
    ordered = sorted(contracts, key=lambda item: (item["path"], item["method"], item["source_paths"][0]))
    print(json.dumps({"root": str(root), "query": args.query, "contracts": ordered}, indent=2))


if __name__ == "__main__":
    main()
