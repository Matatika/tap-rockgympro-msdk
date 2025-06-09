"""Stream type classes for tap-rockgympro."""

from __future__ import annotations

import typing as t
from importlib import resources

from singer_sdk import typing as th  # JSON Schema typing helpers

from tap_rockgympro.client import RockGymProStream
from singer_sdk import pagination
from singer_sdk.streams import RESTStream


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
    def get_url_params(self, context, next_page_token):
        params = super().get_url_params(context, next_page_token)
        params['startDateTime'] = self.config.get('startDateTime')
        return params
    
class CheckinsStream(RockGymProStream):
    parent_stream_type = FacilitiesStream
    name = "checkins"
    path = "/checkins/facility/{code}"
    primary_keys = ["checkinId"]
    replication_key = "postDate"
    schema_filepath = SCHEMAS_DIR /"checkins.json"
    records_jsonpath = "$.checkins[*]"
    def get_url_params(self, context, next_page_token):
        params = super().get_url_params(context, next_page_token)
        params['startDateTime'] = self.config.get('startDateTime')
        return params
    def get_child_context(self, record, context):
        return {'customerGuid':record['customerGuid']}
    
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
        params['customerGuid'] = context['customerGuid']
        return params
