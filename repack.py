# /usr/bin/env python3

import argparse
import json
from pathlib import Path
import sys


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

args = parser.parse_args()


json_filenames = []
for p in args.json_file_or_directory:
    if p.is_dir():
        json_filenames.extend(p.glob("*.json"))
    else:
        json_filenames.append(p)

json_data = {}
for json_file in json_filenames:
    with open(json_file, "r") as f:
        obj = json.load(f)
        json_data[json_file.stem] = obj


def set_key(obj: dict, key: str, value):
    """Set the value of the given key in the object."""
    assert key
    assert isinstance(obj, dict)

    if "." in key:
        head, tail = key.split(".", 1)
        set_key(obj[head], tail, value)
    else:
        obj[key] = value


def is_subtree_export(key, document):
    """Check if the document is a subtree export."""
    if '_' not in key:
        return False
    if isinstance(document, dict) and document.get("type") == "query":
        return False
    return True


for key, document in sorted(json_data.items()):
    print(key, "_" in key, isinstance(document, dict), document.get("type") != "query" if isinstance(document, dict) else "n/a")
    if is_subtree_export(key, document):
        target_key, json_path = key.split("_", 1)
        print(f"-> {target_key} {json_path}")
        set_key(json_data[target_key], json_path, json.dumps(json_data.pop(key)))


njson = "\n".join(json.dumps(obj) for obj in json_data.values())
if args.output:
    with args.output.open("w") as f:
        f.write(njson)
else:
    sys.stdout.write(njson)
