"""RockGymPro tap class."""

from __future__ import annotations

from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers
from typing_extensions import override

from tap_rockgympro import streams

STREAM_TYPES = [
    streams.FacilitiesStream,
    streams.BookingsStream,
    streams.CheckinsStream,
    streams.CustomersStream,
    streams.InvoicesStream,
]


class TapRockGymPro(Tap):
    """RockGymPro tap class."""

    name = "tap-rockgympro"

    config_jsonschema = th.PropertiesList(
        th.Property("api_user", th.StringType, required=True),
        th.Property("api_key", th.StringType, required=True),
        th.Property("startDateTime", th.DateTimeType),
        th.Property(
            "lookback_days",
            th.IntegerType,
            description=(
                "Number of days to subtract from the startDateTime value. "
                "Currently only applies for the invoices stream."
            ),
        ),
    ).to_dict()

    @override
    def discover_streams(self):
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]


if __name__ == "__main__":
    TapRockGymPro.cli()
