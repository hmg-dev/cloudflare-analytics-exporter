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

from elasticsearch._sync.client import IlmClient, IndicesClient
from mockito import when, mock, unstub, verify, ANY, verifyZeroInteractions, eq
from cloudflare.datastore import DataStore
from cloudflare import config
from elasticsearch import Elasticsearch, ApiError
from elastic_transport._models import ApiResponseMeta


class DataStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        unittest.TestCase.setUp(self)
        self.sut = DataStore()
        self.sut.es = mock(Elasticsearch)
        self.dummy_now = datetime.datetime.utcnow()
        self.date_format = "%Y-%m-%dT%H:%M:%S"
        self.dummy_now_str = self.dummy_now.strftime(self.date_format)
        self.dummy_two_weeks_ago = self.dummy_now - datetime.timedelta(days=14)

    def tearDown(self) -> None:
        unittest.TestCase.tearDown(self)
        unstub()

    def test_find_latest_reference_datetime_for_error(self):
        when(self.sut.es).search(index=ANY(str), size=ANY, query=ANY, sort=ANY).thenRaise(
            ApiError(message="TEST", body=None,
                     meta=ApiResponseMeta(status=500, http_version=1, duration=1, node=None, headers=None)))

        result = self.sut.find_latest_reference_datetime()

        self.assertIsNone(result)
        verify(self.sut.es, times=1).search(index=config.es_cf_index, size=1, query={"match_all": {}},
                                            sort={"@timestamp": "desc"})

    def test_find_latest_reference_datetime(self):
        expected_result = datetime.datetime.strptime(self.dummy_now_str, self.date_format)
        when(self.sut.es).search(index=ANY(str), size=ANY, query=ANY, sort=ANY)\
            .thenReturn({"hits": {"total": {"value": 1}, "hits": [{"_source": {"@timestamp": self.dummy_now_str}}]}})

        result = self.sut.find_latest_reference_datetime()

        self.assertIsNotNone(result)
        self.assertEqual(expected_result, result)
        verify(self.sut.es, times=1).search(index=config.es_cf_index, size=1, query={"match_all": {}},
                                            sort={"@timestamp": "desc"})

    def test_find_latest_reference_datetime_for_outdated_reference(self):
        dummy_ref = self.dummy_two_weeks_ago.strftime(self.date_format)
        when(self.sut.es).search(index=ANY(str), size=ANY, query=ANY, sort=ANY)\
            .thenReturn({"hits": {"total": {"value": 1}, "hits": [{"_source": {"@timestamp": dummy_ref}}]}})

        result = self.sut.find_latest_reference_datetime()

        self.assertIsNone(result)
        verify(self.sut.es, times=1).search(index=config.es_cf_index, size=1, query={"match_all": {}},
                                            sort={"@timestamp": "desc"})

    def test__ensure_index_for_existing_index(self):
        ilm_mock = mock(IlmClient)
        indices_mock = mock(IndicesClient)
        self.sut.es.ilm = ilm_mock
        self.sut.es.indices = indices_mock
        when(indices_mock).exists(index=ANY(str), allow_no_indices=ANY).thenReturn("true")

        self.sut._ensure_index()

        verify(indices_mock, times=1).exists(index=config.es_cf_index_pattern, allow_no_indices=False)
        verify(indices_mock, times=0).create(ANY)
        verify(indices_mock, times=0).put_index_template(ANY)
        verifyZeroInteractions(ilm_mock)

    def test__ensure_index_for_not_existing(self):
        ilm_mock = mock(IlmClient)
        indices_mock = mock(IndicesClient)
        self.sut.es.ilm = ilm_mock
        self.sut.es.indices = indices_mock
        when(indices_mock).exists(index=ANY(str), allow_no_indices=ANY).thenReturn("false")
        when(indices_mock).create(index=ANY(str), aliases=ANY)
        when(indices_mock).put_index_template(name=ANY, index_patterns=ANY, template=ANY)
        when(ilm_mock).put_lifecycle(name=ANY, policy=ANY)

        self.sut._ensure_index()

        verify(indices_mock, times=1).exists(index=config.es_cf_index_pattern, allow_no_indices=False)
        verify(indices_mock, times=1).create(index=config.es_cf_initial_index,
                                             aliases={config.es_cf_index: {"is_write_index": True}})
        verify(indices_mock, times=1).put_index_template(name=eq(config.es_cf_index_template),
                                                         index_patterns=[config.es_cf_index_pattern], template=ANY)
        verify(ilm_mock, times=1).put_lifecycle(name=eq(config.es_cf_policy), policy=ANY)
