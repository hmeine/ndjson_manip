# /usr/bin/env python3

import argparse
import json


parser = argparse.ArgumentParser(description="Unpack OSD export ndjson file")
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
parser.add_argument("ndjson_file", type=str, help="Path to the ndjson file to unpack")

args = parser.parse_args()
print(args)


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


with open(args.ndjson_file, "r") as f:
    for line in f:
        obj = json.loads(line)
        if set(obj) == {"exportedCount", "missingRefCount", "missingReferences"}:
            # This is a summary object, skip it
            continue

        for extra_key in (
            "attributes.visState",
            "attributes.kibanaSavedObjectMeta.searchSourceJSON",
            "attributes.fields",
            "attributes.panelsJSON",
        ):
            try:
                # Check if the key exists in the object
                subjson = lookup_key(obj, extra_key)
            except KeyError:
                continue
            else:
                subobj = json.loads(subjson)
                extra_filename = f"{obj['id']}_{extra_key}.json"
                with open(extra_filename, "w") as extra_file:
                    json.dump(subobj, extra_file, indent=4 if args.format else None)
                if args.ref:
                    # Replace the JSON string with a reference
                    set_key(obj, extra_key, {"$ref": extra_filename})

        json_filename = f"{obj['id']}.json"
        with open(json_filename, "w") as json_file:
            json.dump(obj, json_file, indent=4 if args.format else None)
        print(
            json_filename, lookup_key(obj, "type"), lookup_key(obj, "attributes.title")
        )
