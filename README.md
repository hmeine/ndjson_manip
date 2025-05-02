OpenSearch NDJSON Decompiler
============================

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

TODO:

* Add the counterpart of a "packer" that recreates a proper NDJSON file from a
  directory with unpacked JSON files.
* (Optionally?) Use $ref to get rid of the nested JSON data from their parent
  files.
