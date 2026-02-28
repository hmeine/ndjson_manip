# Copyright 2026 by Hans Meine, licensed under the Apache License 2.0
"""CLI and helper utilities for unpacking OpenSearch Dashboards exports."""

import argparse
import json
import os
import re
from pathlib import Path
from typing import Iterable, Sequence

__all__ = [
    "process_ndjson_export",
    "fetch_saved_objects",
    "main",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Unpack OSD export ndjson file into individual JSON files."
    )
    parser.add_argument(
        "--no-format",
        dest="format",
        action="store_false",
        help="Do not pretty-print exported JSON files (default: pretty-print with indent=4)",
    )
    parser.add_argument(
        "--no-ref",
        dest="ref",
        action="store_false",
        help="Do not replace JSON string data with references",
    )
    parser.add_argument(
        "-f",
        "--file",
        dest="ndjson_file",
        type=Path,
        help="Path to the ndjson file to unpack",
    )
    osd_group = parser.add_argument_group(
        "OSD server access",
        "Connection settings for an OpenSearch Dashboards (OSD) instance to be used instead of --file",
    )
    osd_group.add_argument(
        "--url",
        dest="osd_url",
        type=str,
        help="Base URL of the OSD instance to export saved objects from, e.g. http://localhost:5601",
    )
    osd_group.add_argument(
        "--bearer",
        dest="osd_bearer",
        type=str,
        help="Bearer token for authenticating with the OSD instance "
        "(can also be set via OPENSEARCH_BEARER environment variable)",
    )
    osd_group.add_argument(
        "--types",
        dest="object_types",
        type=str,
        help="Comma-separated list of saved object types to export",
        default="dashboard,query",
    )
    osd_group.add_argument(
        "--no-references",
        dest="include_references",
        action="store_false",
        help="Do not include references when exporting saved objects",
    )
    osd_group.add_argument(
        "--tenant",
        dest="osd_tenant",
        type=str,
        help="Security tenant to use when exporting saved objects (default: global)",
    )
    return parser


def lookup_key(obj, key: str):
    """Check if the object has the given key."""
    if not key:
        return obj
    if not isinstance(obj, dict):
        raise KeyError
    head, tail = key.split(".", 1) if "." in key else (key, "")
    value = obj[head]
    return lookup_key(value, tail)


def set_key(obj: dict, key: str, value):
    """Set the value of the given key in the object."""
    assert key
    assert isinstance(obj, dict)

    if "." in key:
        head, tail = key.split(".", 1)
        set_key(obj[head], tail, value)
    else:
        obj[key] = value


def filename_stem(obj):
    result = obj["id"]
    re_illegal = re.compile('[/ ,\\?%*:|"<>]')
    return re_illegal.sub("_", result)


def process_ndjson_export(
    lines: Iterable[str],
    *,
    pretty_print: bool = True,
    use_references: bool = True,
    output_dir: Path | None = None,
) -> list[Path]:
    """Process the NDJSON iterator and write JSON files to the target directory."""

    base_dir = Path(output_dir) if output_dir else Path.cwd()
    created_files: list[Path] = []
    for line in lines:
        obj = json.loads(line)
        if set(obj) == {"exportedCount", "missingRefCount", "missingReferences"}:
            # skip export summary
            continue

        basename = filename_stem(obj)

        for extra_key in (
            "attributes.visState",
            "attributes.kibanaSavedObjectMeta.searchSourceJSON",
            "attributes.fields",
            "attributes.panelsJSON",
        ):
            try:
                subjson = lookup_key(obj, extra_key)
            except KeyError:
                continue
            else:
                subobj = json.loads(subjson)
                extra_filename = f"{basename}_{extra_key}.json"
                extra_path = base_dir / extra_filename
                with extra_path.open("w", encoding="utf-8") as extra_file:
                    json.dump(subobj, extra_file, indent=4 if pretty_print else None)
                created_files.append(extra_path)
                if use_references:
                    set_key(obj, extra_key, {"$ref": extra_filename})

        json_filename = f"{basename}.json"
        json_path = base_dir / json_filename
        with json_path.open("w", encoding="utf-8") as json_file:
            json.dump(obj, json_file, indent=4 if pretty_print else None)
        created_files.append(json_path)
        print(json_filename, lookup_key(obj, "type"), lookup_key(obj, "attributes.title"))

    return created_files


def fetch_saved_objects(
    *,
    osd_url: str,
    bearer_token: str | None,
    object_types: str,
    include_references: bool,
    tenant: str | None,
) -> Iterable[str]:
    """Stream NDJSON from an OpenSearch Dashboards instance."""

    import requests

    body = {
        "type": object_types.split(","),
        "includeReferencesDeep": include_references,
        "excludeExportDetails": True,
    }
    headers = {"osd-xsrf": "true", "Content-Type": "application/json"}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    if tenant:
        headers["securitytenant"] = tenant
    url = f"{osd_url}/api/saved_objects/_export"
    response = requests.post(url, headers=headers, json=body, stream=True)
    response.raise_for_status()
    return response.iter_lines(decode_unicode=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.ndjson_file and args.osd_url:
        parser.error("Error: --file and --url are mutually exclusive")
    if not args.ndjson_file and not args.osd_url:
        parser.error("Error: One of --file or --url must be specified")

    if args.ndjson_file:
        with args.ndjson_file.open("r", encoding="utf-8") as fh:
            process_ndjson_export(
                fh,
                pretty_print=args.format,
                use_references=args.ref,
            )
        return 0

    bearer = args.osd_bearer or os.environ.get("OPENSEARCH_BEARER")
    lines = fetch_saved_objects(
        osd_url=args.osd_url,
        bearer_token=bearer,
        object_types=args.object_types,
        include_references=args.include_references,
        tenant=args.osd_tenant,
    )
    process_ndjson_export(
        lines,
        pretty_print=args.format,
        use_references=args.ref,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
