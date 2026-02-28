# Copyright 2026 by Hans Meine, licensed under the Apache License 2.0
"""CLI and helpers for repacking OpenSearch Dashboards exports."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

from .json_ops import set_key

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

    osd_group = parser.add_argument_group(
        "OSD server access",
        "Connection settings for an OpenSearch Dashboards (OSD) instance to be used instead of --output",
    )
    osd_group.add_argument(
        "--url",
        dest="osd_url",
        type=str,
        help="Base URL of the OSD instance to import saved objects into, e.g. http://localhost:5601",
    )
    osd_group.add_argument(
        "--bearer",
        dest="osd_bearer",
        type=str,
        help="Bearer token for authenticating with the OSD instance "
        "(can also be set via OPENSEARCH_BEARER environment variable)",
    )
    osd_group.add_argument(
        "--tenant",
        dest="osd_tenant",
        type=str,
        help="Security tenant to use when importing saved objects (default: global)",
    )
    osd_group.add_argument(
        "--overwrite",
        dest="overwrite",
        action="store_true",
        help="Overwrite existing saved objects with the same ID (default: do not overwrite)",
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


def push_saved_objects(
    *,
    saved_objects: str,
    osd_url: str,
    bearer_token: str | None,
    tenant: str | None,
    overwrite: bool = False,
) -> dict:
    """Stream NDJSON from an OpenSearch Dashboards instance."""

    import requests

    headers = {"osd-xsrf": "true"}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    if tenant:
        headers["securitytenant"] = tenant
    params = {"overwrite": "true"} if overwrite else {}
    url = f"{osd_url}/api/saved_objects/_import"
    form_data = {
        "file": (
            "export.ndjson",
            saved_objects.encode("utf-8"),
            "application/ndjson",
        )
    }
    response = requests.post(
        url, headers=headers, files=form_data, params=params, stream=True
    )
    response.raise_for_status()
    result = response.json()
    sys.stdout.write(f"{result.get('successCount', 0)} objects imported successfully.\n")
    for success in result.get("successResults", []):
        sys.stdout.write(f"  {success.get('type')}: {success.get('meta', {}).get('title')}\n")
    if errors := result.get("errors", []):
        sys.stderr.write(f"ERROR: {len(errors)} objects failed to import:\n")
        for error in errors:
            sys.stderr.write(f"  {error.get('error', {}).get('type', 'error')} with {error.get('type')}: {error.get('meta', {}).get('title')}\n")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.output and args.osd_url:
        parser.error("--output and --url are mutually exclusive")

    ndjson = repack_documents(args.json_file_or_directory)
    if args.output:
        args.output.write_text(ndjson, encoding="utf-8")
    elif args.osd_url:
        bearer = args.osd_bearer or os.environ.get("OPENSEARCH_BEARER")
        response = push_saved_objects(
            saved_objects=ndjson,
            osd_url=args.osd_url,
            bearer_token=bearer,
            tenant=args.osd_tenant,
            overwrite=args.overwrite,
        )
        if not response.get("success"):
            return 1
    else:
        sys.stdout.write(ndjson)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
