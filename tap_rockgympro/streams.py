"""Stream type classes for tap-rockgympro."""

from __future__ import annotations

import typing as t
from importlib import resources

from singer_sdk import typing as th  # JSON Schema typing helpers

from tap_rockgympro.client import RockGymProStream
from singer_sdk import pagination
from singer_sdk.streams import RESTStream
from typing_extensions import override
from tap_rockgympro import BufferDeque

# TODO: Delete this is if not using json files for schema definition
SCHEMAS_DIR = resources.files(__package__) / "schemas"
# TODO: - Override `UsersStream` and `GroupsStream` with your own stream definition.
#       - Copy-paste as many times as needed to create multiple stream types.

class FacilitiesStream(RockGymProStream):
    name = "facilities"
    path = "/facilities"
    primary_keys = ["code"]
    #replication_key = "bookingDate"
    schema_filepath = SCHEMAS_DIR /"facilties.json"
    records_jsonpath = "$.facilities.*"
    def get_new_paginator(self):
        return RESTStream.get_new_paginator(self)
    def get_child_context(self, record, context):
        return {'code':record['code']}
    
class BookingsStream(RockGymProStream):
    parent_stream_type = FacilitiesStream
    name = "bookings"
    path = "/bookings/facility/{code}"
    primary_keys = ["booking_id"]
    replication_key = "bookingDate"
    schema_filepath = SCHEMAS_DIR /"bookings.json"
    records_jsonpath = "$.bookings[*]"
    
class CheckinsStream(RockGymProStream):
    parent_stream_type = FacilitiesStream
    name = "checkins"
    path = "/checkins/facility/{code}"
    primary_keys = ["checkinId"]
    replication_key = "postDate"
    schema_filepath = SCHEMAS_DIR /"checkins.json"
    records_jsonpath = "$.checkins[*]"
    
    @override
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.customer_guids_buffer = BufferDeque(maxlen=150)

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
    parent_stream_type = CheckinsStream
    name = "customers"
    path = "/customers"
    primary_keys = ["customerGuid"]
    replication_key = "lastRecordEdit"
    schema_filepath = SCHEMAS_DIR /"customers.json"
    records_jsonpath = "$.customer[*]"
    def get_url_params(self, context, next_page_token):
        params = super().get_url_params(context, next_page_token)
        params['customerGuid'] = context['customer_guids']
        return params

class InvoicesStream(RockGymProStream):
    parent_stream_type = FacilitiesStream
    name = "invoices"
    path = "/invoices/facility/{code}"
    primary_keys = ["invoiceId"]
    schema_filepath = SCHEMAS_DIR /"invoices.json"
    records_jsonpath = "$.invoices[*]"