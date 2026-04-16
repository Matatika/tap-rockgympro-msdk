"""Stream type classes for tap-rockgympro."""

from __future__ import annotations

from datetime import datetime, timedelta
from importlib import resources

from singer_sdk.streams import RESTStream
from typing_extensions import override

from tap_rockgympro import BufferDeque
from tap_rockgympro.client import RockGymProStream

SCHEMAS_DIR = resources.files(__package__) / "schemas"


class FacilitiesStream(RockGymProStream):
    """Facilities stream."""

    name = "facilities"
    path = "/facilities"
    primary_keys = ("code",)
    # replication_key = "bookingDate"
    schema_filepath = SCHEMAS_DIR / "facilties.json"
    records_jsonpath = "$.facilities.*"

    @override
    def get_new_paginator(self):
        return RESTStream.get_new_paginator(self)

    @override
    def get_child_context(self, record, context):
        return {"code": record["code"]}


class BookingsStream(RockGymProStream):
    """Bookings stream."""

    parent_stream_type = FacilitiesStream
    name = "bookings"
    path = "/bookings/facility/{code}"
    primary_keys = ("bookingId",)
    replication_key = "bookingDate"
    schema_filepath = SCHEMAS_DIR / "bookings.json"
    records_jsonpath = "$.bookings[*]"


class CheckinsStream(RockGymProStream):
    """Check-ins stream."""

    parent_stream_type = FacilitiesStream
    name = "checkins"
    path = "/checkins/facility/{code}"
    primary_keys = ("checkinId",)
    replication_key = "postDate"
    schema_filepath = SCHEMAS_DIR / "checkins.json"
    records_jsonpath = "$.checkins[*]"


class InvoicesStream(RockGymProStream):
    """Invoices stream."""

    parent_stream_type = FacilitiesStream
    name = "invoices"
    path = "/invoices/facility/{code}"
    primary_keys = ("invoiceId",)
    replication_key = "invoicePostDate"
    schema_filepath = SCHEMAS_DIR / "invoices.json"
    records_jsonpath = "$.invoices[*]"

    @override
    def get_url_params(self, context, next_page_token):
        params = super().get_url_params(context, next_page_token)

        start_date_time = params.get("startDateTime")
        lookback_days = self.config.get("lookback_days")

        if start_date_time and lookback_days:
            start_dt = datetime.fromisoformat(start_date_time)
            offset_dt = start_dt - timedelta(days=lookback_days)
            params["startDateTime"] = offset_dt.strftime("%Y-%m-%d %H:%M:%S")

        return params

    @override
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.customer_guids_buffer = BufferDeque(
            maxlen=25
        )  # Batch size limit set by rockgympro

    @override
    def parse_response(self, response):
        for record in super().parse_response(response):
            yield record

        # make sure we process the remaining buffer entries
        self.customer_guids_buffer.finalize()
        yield record  # yield last record again to force child context generation

    @override
    def generate_child_contexts(self, record, context):
        self.customer_guids_buffer.append(record["customerGuid"])

        with self.customer_guids_buffer as buf:
            if buf.flush:
                yield {"customer_guids": buf}


class CustomersStream(RockGymProStream):
    """Customers stream."""

    parent_stream_type = InvoicesStream
    name = "customers"
    path = "/customers"
    primary_keys = ("customerGuid",)
    replication_key = "lastRecordEdit"
    schema_filepath = SCHEMAS_DIR / "customers.json"
    records_jsonpath = "$.customer[*]"

    # we don't want to store any state bookmarks for the child stream
    state_partitioning_keys = ()

    @override
    def get_url_params(self, context, next_page_token):
        params = super().get_url_params(context, next_page_token)
        params["customerGuid"] = ",".join(context["customer_guids"])
        return params
