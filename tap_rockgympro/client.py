"""REST client handling, including RockGymProStream base class."""

from __future__ import annotations

import decimal
import typing as t
from importlib import resources

from requests.auth import HTTPBasicAuth
from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.streams import RESTStream

from tap_rockgympro.pagination import RockGymProPaginator

if t.TYPE_CHECKING:
    import requests
    from singer_sdk.helpers.types import Context


SCHEMAS_DIR = resources.files(__package__) / "schemas"


class RockGymProStream(RESTStream):
    """RockGymPro stream class."""

    # Update this value if necessary or override `parse_response`.
    records_jsonpath = "$[*]"

    # Update this value if necessary or override `get_new_paginator`.
    next_page_token_jsonpath = "$.next_page"  # noqa: S105

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return "https://api.rockgympro.com/v1"

    @property
    def authenticator(self) -> HTTPBasicAuth:
        return HTTPBasicAuth(
            username=self.config.get("api_user"), password=self.config.get("api_key")
        )

    def get_new_paginator(self):
        return RockGymProPaginator()

    def get_url_params(
        self,
        context: Context | None,
        next_page_token: t.Any | None,  # noqa: ANN401
    ) -> dict[str, t.Any]:
        """Return a dictionary of values to be used in URL parameterization.

        Args:
            context: The stream context.
            next_page_token: The next page index or value.

        Returns:
            A dictionary of URL query parameters.
        """
        params: dict = {}
        if next_page_token:
            params["page"] = next_page_token
        if self.replication_key:
            params["sort"] = "asc"
            params["order_by"] = self.replication_key
        params["limit"] = 200
        params["startDateTime"] = self.get_starting_replication_key_value(
            context
        ) or self.config.get("startDateTime")
        return params

    def post_process(self, row, context=None):
        if row.get("cancelledOn") == "0000-00-00 00:00:00":
            row["cancelledOn"] = None
        if row.get("checkoutPostDate") == "0000-00-00 00:00:00":
            row["checkoutPostDate"] = None
        return row

    def backoff_max_tries(self):
        return 8
