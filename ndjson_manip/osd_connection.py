# Copyright 2026 by Hans Meine, licensed under the Apache License 2.0
"""Helper functions for connecting to OpenSearch Dashboards directly."""

import argparse
import base64
import os
from dataclasses import dataclass


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
        "--user",
        "-u",
        dest="osd_user",
        type=str,
        help="Username for authenticating with the OSD instance "
        "(can also be set via OPENSEARCH_USER environment variable)",
    )
    osd_group.add_argument(
        "--password",
        "-p",
        dest="osd_password",
        type=str,
        help="Password for authenticating with the OSD instance "
        "(can also be set via OPENSEARCH_PASSWORD environment variable)",
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


@dataclass
class OSDConnectionSettings:
    url: str | None = None
    verify_ssl: bool = True
    user: str | None = None
    password: str | None = None
    bearer: str | None = None
    tenant: str | None = None

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "OSDConnectionSettings":
        return cls(
            url=args.osd_url,
            verify_ssl=args.verify_ssl,
            user=args.osd_user or os.environ.get("OPENSEARCH_USER"),
            password=args.osd_password or os.environ.get("OPENSEARCH_PASSWORD"),
            bearer=args.osd_bearer or os.environ.get("OPENSEARCH_BEARER"),
            tenant=args.osd_tenant,
        )

    def headers(self) -> dict[str, str]:
        headers = {"osd-xsrf": "true"}
        if self.bearer:
            headers["Authorization"] = f"Bearer {self.bearer}"
        elif self.user and self.password:
            headers["Authorization"] = f"Basic {base64.b64encode(f'{self.user}:{self.password}'.encode()).decode()}"
        if self.tenant:
            headers["securitytenant"] = self.tenant
        return headers
