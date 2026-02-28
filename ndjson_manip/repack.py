# Copyright 2026 by Hans Meine, licensed under the Apache License 2.0
"""CLI and helpers for repacking OpenSearch Dashboards exports."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

__all__ = ["repack_documents", "main"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Repack OSD export ndjson file from unpacked JSON files"
    )
    parser.add_argument("--output", "-o", type=Path, help="Output NDJSON file name")
    parser.add_argument(
        "json_file_or_directory",
        type=Path,
        help="Path(s) to the JSON files (or directory)",
        nargs="+",
    )
    return parser


def _expand_json_inputs(paths: Sequence[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(sorted(path.glob("*.json")))
        else:
            files.append(path)
    return files


def _load_documents(json_files: Iterable[Path]) -> dict[str, Any]:
    documents: dict[str, Any] = {}
    for json_file in json_files:
        with json_file.open("r", encoding="utf-8") as fh:
            documents[json_file.stem] = json.load(fh)
    return documents


def set_key(obj: dict, key: str, value):
    """Set the value of the given key in the object."""
    assert key
    assert isinstance(obj, dict)

    if "." in key:
        head, tail = key.split(".", 1)
        set_key(obj[head], tail, value)
    else:
        obj[key] = value


def _is_subtree_export(key: str, document) -> bool:
    """Check if the document is a subtree export."""
    if "_" not in key:
        return False
    if isinstance(document, dict) and document.get("type") == "query":
        return False
    return True


def repack_documents(json_inputs: Sequence[Path]) -> str:
    """Return the NDJSON string generated from the provided JSON files."""

    json_data = _load_documents(_expand_json_inputs(json_inputs))
    for key, document in sorted(list(json_data.items())):
        if _is_subtree_export(key, document):
            target_key, json_path = key.split("_", 1)
            set_key(json_data[target_key], json_path, json.dumps(json_data.pop(key)))

    return "\n".join(json.dumps(obj) for obj in json_data.values())


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    ndjson = repack_documents(args.json_file_or_directory)
    if args.output:
        args.output.write_text(ndjson, encoding="utf-8")
    else:
        sys.stdout.write(ndjson)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
