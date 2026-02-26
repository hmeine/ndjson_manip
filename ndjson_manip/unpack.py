# /usr/bin/env python3

import argparse
import json
import os
import re


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
    type=str,
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


def process_ndjson_export(f):
    for line in f:
        obj = json.loads(line)
        if set(obj) == {"exportedCount", "missingRefCount", "missingReferences"}:
            # This is a summary object, skip it
            continue

        basename = filename_stem(obj)

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
                extra_filename = f"{basename}_{extra_key}.json"
                with open(extra_filename, "w") as extra_file:
                    json.dump(subobj, extra_file, indent=4 if args.format else None)
                if args.ref:
                    # Replace the JSON string with a reference
                    set_key(obj, extra_key, {"$ref": extra_filename})

        json_filename = f"{basename}.json"
        with open(json_filename, "w") as json_file:
            json.dump(obj, json_file, indent=4 if args.format else None)
        print(
            json_filename, lookup_key(obj, "type"), lookup_key(obj, "attributes.title")
        )


if args.ndjson_file:
    if args.osd_url:
        parser.error("Error: --file and --url are mutually exclusive")
    with open(args.ndjson_file, "r") as f:
        process_ndjson_export(f)
else:
    if not args.osd_url:
        parser.error("Error: One of --file or --url must be specified")

    import requests
    body = {
        "type": args.object_types.split(","),
        "includeReferencesDeep": args.include_references,
        "excludeExportDetails": True,
    }
    headers = {"osd-xsrf": "true", "Content-Type": "application/json"}
    bearer_token = args.osd_bearer or os.environ.get("OPENSEARCH_BEARER")
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    if args.osd_tenant:
        headers["securitytenant"] = args.osd_tenant
    url = f"{args.osd_url}/api/saved_objects/_export"
    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    process_ndjson_export(response.iter_lines(decode_unicode=True))
