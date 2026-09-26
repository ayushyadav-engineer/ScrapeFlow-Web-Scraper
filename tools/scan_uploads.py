from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

hits: list[tuple[Path, int]] = []
for path in (ROOT / "app").rglob("*.py"):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "files":
            hits.append((path, node.lineno))

if hits:
    print("File-upload code detected; a dedicated upload safety review is required:")
    for path, line in hits:
        print(f" - {path.relative_to(ROOT)}:{line}")
    raise SystemExit(2)

print("Upload safety scan passed: no request.files/FileStorage upload handlers are present in the application.")
