"""REST client handling, including RockGymProStream base class."""

from __future__ import annotations

import typing as t
from datetime import datetime, timedelta
from importlib import resources

from requests.auth import HTTPBasicAuth
from singer_sdk.streams import RESTStream
from typing_extensions import override

from tap_rockgympro.pagination import RockGymProPaginator

if t.TYPE_CHECKING:
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

    @override
    @property
    def authenticator(self) -> HTTPBasicAuth:
        return HTTPBasicAuth(
            username=self.config.get("api_user"),
            password=self.config.get("api_key"),
        )

    @override
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

    def apply_lookback(self, params: dict[str, t.Any]) -> dict[str, t.Any]:
        """Offset ``startDateTime`` backwards by the ``lookback_days`` setting.

        This lets a stream re-fetch records that were edited after they were
        last replicated but whose replication key is older than the current
        bookmark. No-op when ``lookback_days`` is unset or ``startDateTime``
        is not present.

        Args:
            params: The URL query parameters to adjust in place.

        Returns:
            The (possibly) adjusted URL query parameters.
        """
        start_date_time = params.get("startDateTime")
        lookback_days = self.config.get("lookback_days")

        if start_date_time and lookback_days:
            start_dt = datetime.fromisoformat(start_date_time)
            offset_dt = start_dt - timedelta(days=lookback_days)
            params["startDateTime"] = offset_dt.strftime("%Y-%m-%d %H:%M:%S")

        return params

    @override
    def post_process(self, row, context=None):
        if row.get("cancelledOn") == "0000-00-00 00:00:00":
            row["cancelledOn"] = None
        if row.get("checkoutPostDate") == "0000-00-00 00:00:00":
            row["checkoutPostDate"] = None
        return row

    @override
    def backoff_max_tries(self):
        return 8
