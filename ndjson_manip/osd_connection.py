# Copyright 2026 by Hans Meine, licensed under the Apache License 2.0
"""Helper functions for connecting to OpenSearch Dashboards directly."""

import argparse


def build_osd_parser_group(parser: argparse.ArgumentParser) -> argparse._ArgumentGroup:
    osd_group = parser.add_argument_group(
        "OSD server access",
        "Connection settings for an OpenSearch Dashboards (OSD) instance",
    )
    osd_group.add_argument(
        "--url",
        dest="osd_url",
        type=str,
        help="Base URL of the OSD instance to connect to, e.g. http://localhost:5601",
    )
    osd_group.add_argument(
        "--insecure",
        dest="verify_ssl",
        action="store_false",
        default=True,
        help="Disable SSL certificate verification when connecting to OSD",
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
        help="Security tenant to use when connecting to the OSD instance (default: global)",
    )
    return osd_group
