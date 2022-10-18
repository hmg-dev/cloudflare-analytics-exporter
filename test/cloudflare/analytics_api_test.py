# Copyright (C) 2022, Martin Drößler <m.droessler@handelsblattgroup.com>
# Copyright (C) 2022, Handelsblatt GmbH
#
# This file is part of cloudflare-analytics-exporter
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import unittest
import datetime
import json
import os
import gql

import gql.transport.requests as gql_transport
from graphql import DocumentNode
from mockito import when, mock, unstub, verify, ANY
from cloudflare import analytics_api as sut
from cloudflare import config


class AnalyticsApiTest(unittest.TestCase):
    def setUp(self) -> None:
        unittest.TestCase.setUp(self)
        self.dummy_datetime = datetime.datetime.strptime("2022-09-20T12:12:00", "%Y-%m-%dT%H:%M:%S")

    def tearDown(self) -> None:
        unittest.TestCase.tearDown(self)
        unstub()

    def test_read_gql_query_from_file_for_invalid_filename(self):
        with self.assertRaises(Exception) as ctx:
            sut.read_gql_query_from_file("invalid")

        self.assertRegex(str(ctx.exception), "\\[Errno 2\\] No such file or directory:.*")

    def test_read_gql_query_from_file_for_zone_query(self):
        result = sut.read_gql_query_from_file("zone-totals.graphql")

        self.assertIsNotNone(result)

    @staticmethod
    def _create_dummy_response():
        with open(os.path.dirname(__file__) + f"/../resources/dummy-response.json", 'r') as f:
            gql_query = f.read()

        return json.loads(gql_query)

    def test_fetch_cloudflare_analytics(self):
        expected_doc_amount = 106
        expected_cf_headers = {"X-AUTH-EMAIL": config.cf_api_user, "Authorization": f"Bearer None"}
        expected_parameters = {
            "limit": 9999,
            "mintime": "2022-09-20T12:12:00Z",
            "maxtime": "2022-09-20T12:13:01Z",
            "zoneIDs": list(config.zones.keys())
        }

        dummy_client = mock(gql.Client)
        dummy_transport = mock(gql_transport.RequestsHTTPTransport)
        dummy_query = mock(DocumentNode)

        when(gql_transport).RequestsHTTPTransport(url=ANY(), verify=ANY(), retries=ANY(), headers=ANY())\
            .thenReturn(dummy_transport)
        when(gql).Client(...).thenReturn(dummy_client)
        when(gql).gql(ANY()).thenReturn(dummy_query)
        when(dummy_client).execute(...).thenReturn(self._create_dummy_response())

        result = sut.fetch_cloudflare_analytics(self.dummy_datetime)

        self.assertIsNotNone(result)
        self.assertEqual(expected_doc_amount, len(result))

        verify(gql_transport, times=1).RequestsHTTPTransport(
            url=config.cf_api_endpoint, verify=True, retries=3, headers=expected_cf_headers)
        verify(gql, times=1).Client(transport=dummy_transport, fetch_schema_from_transport=False)
        verify(gql, times=1).gql(ANY(str))
        verify(dummy_client, times=1).execute(dummy_query, variable_values=expected_parameters)
