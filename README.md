OpenSearch NDJSON Unpacker
==========================

OpenSearch Dashboards (OSD) allows to export "saved objects" (most notably
dashboards, visualizations, and index patterns) as .ndjson files.  There are a
few aspects that make these hard to read / process:

* .ndjson (newline-delimited JSON objects) is slightly less common than JSON
  itself, and not every formatter may be able to work with it.

* Normal JSON formatting would introduce newlines, and although the JSON data
  would still be unambiguously parsable, NDJSON parsers may assume that each
  line is exactly one complete JSON object.

* Furthermore, OSD has a few values in the JSON data that are itself
  string-encoded JSON data.  In fact, much of the "interesting" values that I
  want to modify in exported data are inside such JSON strings, which are
  particularly hard to read and edit since they are not formatted by JSON
  formatting and contain lots of extra quoting characters.

As a solution to these problems, I wrote this quick script to "unpack" the
NDJSON into properly formatted JSON files, including an extraction of the nested
JSON strings.

The result can be version-controlled (with readable diffs after changes),
possibly edited by hand, and eventually uploaded again using the "ndjson-repack"
script that recreates a proper NDJSON file from a directory with unpacked JSON
files.

Example
-------

Let's take one of OpenSearch's examples, the flights dashboard, as an example.
The [`export.ndjson`](tests/export-flights.ndjson) is 49KB and contains 22 lines
(including the default export summary in the last line), many of which look like
this:

```json
{"attributes":{"description":"","kibanaSavedObjectMeta":{"searchSourceJSON":"{\"filter\":[{\"meta\":{\"negate\":true,\"disabled\":false,\"alias\":null,\"type\":\"phrase\",\"key\":\"FlightDelayMin\",\"value\":\"0\",\"params\":{\"query\":0,\"type\":\"phrase\"},\"indexRefName\":\"kibanaSavedObjectMeta.searchSourceJSON.filter[0].meta.index\"},\"query\":{\"match\":{\"FlightDelayMin\":{\"query\":0,\"type\":\"phrase\"}}},\"$state\":{\"store\":\"appState\"}}],\"query\":{\"query\":\"\",\"language\":\"kuery\"},\"indexRefName\":\"kibanaSavedObjectMeta.searchSourceJSON.index\"}"},"title":"[Flights] Delay Buckets","uiStateJSON":"{\"vis\":{\"legendOpen\":false}}","version":1,"visState":"{\"title\":\"[Flights] Delay Buckets\",\"type\":\"histogram\",\"params\":{\"type\":\"histogram\",\"grid\":{\"categoryLines\":false,\"style\":{\"color\":\"#eee\"}},\"categoryAxes\":[{\"id\":\"CategoryAxis-1\",\"type\":\"category\",\"position\":\"bottom\",\"show\":true,\"style\":{},\"scale\":{\"type\":\"linear\"},\"labels\":{\"show\":true,\"truncate\":100},\"title\":{}}],\"valueAxes\":[{\"id\":\"ValueAxis-1\",\"name\":\"LeftAxis-1\",\"type\":\"value\",\"position\":\"left\",\"show\":true,\"style\":{},\"scale\":{\"type\":\"linear\",\"mode\":\"normal\"},\"labels\":{\"show\":true,\"rotate\":0,\"filter\":false,\"truncate\":100},\"title\":{\"text\":\"Count\"}}],\"seriesParams\":[{\"show\":\"true\",\"type\":\"histogram\",\"mode\":\"stacked\",\"data\":{\"label\":\"Count\",\"id\":\"1\"},\"valueAxis\":\"ValueAxis-1\",\"drawLinesBetweenPoints\":true,\"showCircles\":true}],\"addTooltip\":true,\"addLegend\":true,\"legendPosition\":\"right\",\"times\":[],\"addTimeMarker\":false},\"aggs\":[{\"id\":\"1\",\"enabled\":true,\"type\":\"count\",\"schema\":\"metric\",\"params\":{}},{\"id\":\"2\",\"enabled\":true,\"type\":\"histogram\",\"schema\":\"segment\",\"params\":{\"field\":\"FlightDelayMin\",\"interval\":30,\"extended_bounds\":{},\"customLabel\":\"Flight Delay Minutes\"}}]}"},"id":"9886b410-4c8b-11e8-b3d7-01146121b73d","migrationVersion":{"visualization":"7.10.0"},"references":[{"id":"d3d7af60-4c81-11e8-b3d7-01146121b73d","name":"kibanaSavedObjectMeta.searchSourceJSON.index","type":"index-pattern"},{"id":"d3d7af60-4c81-11e8-b3d7-01146121b73d","name":"kibanaSavedObjectMeta.searchSourceJSON.filter[0].meta.index","type":"index-pattern"}],"type":"visualization","updated_at":"2026-03-02T19:53:57.528Z","version":"WzI5LDVd"}
```

After unpacking (`ndjson-unpack -f ../export-flights.ndjson` in a fresh
directory), we get [many JSON files](tests/export-flights/), three of which
correspond to the above line.  The main file is
[`9886b410-4c8b-11e8-b3d7-01146121b73d.json`](tests/export-flights/9886b410-4c8b-11e8-b3d7-01146121b73d.json):

```json
{
    "attributes": {
        "description": "",
        "kibanaSavedObjectMeta": {
            "searchSourceJSON": {
                "$ref": "9886b410-4c8b-11e8-b3d7-01146121b73d_attributes.kibanaSavedObjectMeta.searchSourceJSON.json"
            }
        },
        "title": "[Flights] Delay Buckets",
        "uiStateJSON": "{\"vis\":{\"legendOpen\":false}}",
        "version": 1,
        "visState": {
            "$ref": "9886b410-4c8b-11e8-b3d7-01146121b73d_attributes.visState.json"
        }
    },
    "id": "9886b410-4c8b-11e8-b3d7-01146121b73d",
    "migrationVersion": {
        "visualization": "7.10.0"
    },
    "references": [
        {
            "id": "d3d7af60-4c81-11e8-b3d7-01146121b73d",
            "name": "kibanaSavedObjectMeta.searchSourceJSON.index",
            "type": "index-pattern"
        },
        {
            "id": "d3d7af60-4c81-11e8-b3d7-01146121b73d",
            "name": "kibanaSavedObjectMeta.searchSourceJSON.filter[0].meta.index",
            "type": "index-pattern"
        }
    ],
    "type": "visualization",
    "updated_at": "2026-03-02T19:53:57.528Z",
    "version": "WzI5LDVd"
}
```

Instead of the `searchSourceJSON` and `visState` values being string-encoded
JSON, their content is exported into separate JSON files, and the main file
contains a reference to those files.  The content of
[`9886b410-4c8b-11e8-b3d7-01146121b73d_attributes.kibanaSavedObjectMeta.searchSourceJSON.json`](tests/export-flights/9886b410-4c8b-11e8-b3d7-01146121b73d_attributes.kibanaSavedObjectMeta.searchSourceJSON.json)
is:

```json
{
    "filter": [
        {
            "meta": {
                "negate": true,
                "disabled": false,
                "alias": null,
                "type": "phrase",
                "key": "FlightDelayMin",
                "value": "0",
                "params": {
                    "query": 0,
                    "type": "phrase"
                },
                "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.filter[0].meta.index"
            },
            "query": {
                "match": {
                    "FlightDelayMin": {
                        "query": 0,
                        "type": "phrase"
                    }
                }
            },
            "$state": {
                "store": "appState"
            }
        }
    ],
    "query": {
        "query": "",
        "language": "kuery"
    },
    "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index"
}
```

and the content of [`9886b410-4c8b-11e8-b3d7-01146121b73d_attributes.visState.json`](tests/export-flights/9886b410-4c8b-11e8-b3d7-01146121b73d_attributes.visState.json) is:

```json
{
    "title": "[Flights] Delay Buckets",
    "type": "histogram",
    "params": {
        "type": "histogram",
        "grid": {
            "categoryLines": false,
            "style": {
                "color": "#eee"
            }
        },
        "categoryAxes": [
            {
                "id": "CategoryAxis-1",
                "type": "category",
                "position": "bottom",
                "show": true,
                "style": {},
                "scale": {
                    "type": "linear"
                },
                "labels": {
                    "show": true,
                    "truncate": 100
                },
                "title": {}
            }
        ],
        "valueAxes": [
            {
                "id": "ValueAxis-1",
                "name": "LeftAxis-1",
                "type": "value",
                "position": "left",
                "show": true,
                "style": {},
                "scale": {
                    "type": "linear",
                    "mode": "normal"
                },
                "labels": {
                    "show": true,
                    "rotate": 0,
                    "filter": false,
                    "truncate": 100
                },
                "title": {
                    "text": "Count"
                }
            }
        ],
        "seriesParams": [
            {
                "show": "true",
                "type": "histogram",
                "mode": "stacked",
                "data": {
                    "label": "Count",
                    "id": "1"
                },
                "valueAxis": "ValueAxis-1",
                "drawLinesBetweenPoints": true,
                "showCircles": true
            }
        ],
        "addTooltip": true,
        "addLegend": true,
        "legendPosition": "right",
        "times": [],
        "addTimeMarker": false
    },
    "aggs": [
        {
            "id": "1",
            "enabled": true,
            "type": "count",
            "schema": "metric",
            "params": {}
        },
        {
            "id": "2",
            "enabled": true,
            "type": "histogram",
            "schema": "segment",
            "params": {
                "field": "FlightDelayMin",
                "interval": 30,
                "extended_bounds": {},
                "customLabel": "Flight Delay Minutes"
            }
        }
    ]
}
```

These files are much easier to read and edit, and the diffs when versioning them
in git are more meaningful and easier to review.  (Furthermore, you can use the
`--remove-version` option to remove the `version` and `updated_at` fields, in
case you want to suppress semantically irrelevant changes.)

TODOs
-----

* support exporting only a single dashboard (instead of all dashboards / objects
  of the same type)
