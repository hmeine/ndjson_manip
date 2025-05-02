#/usr/bin/env python3

import argparse
import json


parser = argparse.ArgumentParser(description='Unpack OSD export ndjson file')

parser.add_argument('ndjson_file', type=str, help='Path to the ndjson file to unpack')
args = parser.parse_args()

def lookup_key(obj, key: str):
    """Check if the object has the given key."""
    if not key:
        return obj
    if not isinstance(obj, dict):
        raise KeyError
    head, tail = key.split(".", 1) if "." in key else (key, "")
    value = obj[head]
    return lookup_key(value, tail)

with open(args.ndjson_file, 'r') as f:
    for line in f:
        obj = json.loads(line)
        if set(obj) == {"exportedCount","missingRefCount","missingReferences"}:
            # This is a summary object, skip it
            continue

        json_filename = f"{obj['id']}.json"
        with open(json_filename, 'w') as json_file:
            json.dump(obj, json_file)#, indent=4)
        print(json_filename, lookup_key(obj, "type"), lookup_key(obj, "attributes.title"))

        for extra_key in (
            "attributes.visState",
            "attributes.kibanaSavedObjectMeta.searchSourceJSON",
            "attributes.fields",
            "attributes.panelsJSON"
        ):
            try:
                # Check if the key exists in the object
                subjson = lookup_key(obj, extra_key)
            except KeyError:
                continue
            else:
                subobj = json.loads(subjson)
                extra_filename = f"{obj['id']}_{extra_key}.json"
                with open(extra_filename, 'w') as extra_file:
                    json.dump(subobj, extra_file, indent=4)
