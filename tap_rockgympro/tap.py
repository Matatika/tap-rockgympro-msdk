"""RockGymPro tap class."""

from __future__ import annotations

from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers

# TODO: Import your custom stream types here:
from tap_rockgympro import streams
from tap_rockgympro.pagination import RockGymProPaginator

STREAM_TYPES = [
    streams.FacilitiesStream
    , streams.BookingsStream
    , streams.CheckinsStream
    , streams.CustomersStream
    , streams.InvoicesStream
]

class TapRockGymPro(Tap):
    """RockGymPro tap class."""

    name = "tap-rockgympro"

    # TODO: Update this section with the actual config values you expect:
    config_jsonschema = th.PropertiesList(
        th.Property("api_user", th.StringType, required=True),
        th.Property("api_key", th.StringType, required=True),
        th.Property("startDateTime", th.DateTimeType)
    ).to_dict()

    def discover_streams(self):
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]

if __name__ == "__main__":
    TapRockGymPro.cli()
