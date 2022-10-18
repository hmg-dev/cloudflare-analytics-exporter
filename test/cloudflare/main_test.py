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
import time

from mockito import when, mock, unstub, verify, ANY
from cloudflare import analytics_api, datastore
from cloudflare import main as sut
from cloudflare import no_concurrency


class MainTest(unittest.TestCase):
    def setUp(self) -> None:
        unittest.TestCase.setUp(self)
        self.dummy_datetime = datetime.datetime.strptime("2022-09-20T12:12:00", "%Y-%m-%dT%H:%M:%S")
        self.dummy_ds = mock(datastore.DataStore)

    def tearDown(self) -> None:
        unittest.TestCase.tearDown(self)
        unstub()

    def test_run_fetch_and_push(self):
        dummy_data = [{"data": "dummy"}, {"data": "narf"}]
        when(analytics_api).fetch_cloudflare_analytics(ANY).thenReturn(dummy_data)
        when(time).sleep(ANY)
        when(self.dummy_ds).store_documents(...)

        result = sut.run_fetch_and_push(self.dummy_datetime, self.dummy_ds)

        self.assertIsNotNone(result)
        self.assertNotEqual(result, self.dummy_datetime)

        verify(analytics_api, times=1).fetch_cloudflare_analytics(ANY)
        verify(self.dummy_ds, times=1).store_documents(docs=dummy_data)
        verify(time, times=1).sleep(5)

    def test_main(self):
        dummy_concurrency_checker = mock()

        when(self.dummy_ds).connect()
        when(self.dummy_ds).find_latest_reference_datetime().thenReturn(self.dummy_datetime)
        when(no_concurrency).NoConcurrency().thenReturn(dummy_concurrency_checker)
        when(sut).still_active(ANY).thenReturn(True).thenReturn(False)
        when(sut).run_fetch_and_push(ANY, ANY)
        when(sut).verify_allowed_to_run(ANY)

        sut.main(self.dummy_ds)

        verify(self.dummy_ds, times=1).connect()
        verify(self.dummy_ds, times=1).find_latest_reference_datetime()
        verify(sut, times=2).still_active(dummy_concurrency_checker)
        verify(sut, times=1).run_fetch_and_push(self.dummy_datetime, self.dummy_ds)
        verify(sut, times=1).verify_allowed_to_run(dummy_concurrency_checker)

    @staticmethod
    def test_verify_allowed_to_run():
        dummy_concurrency_checker = mock()
        when(dummy_concurrency_checker).is_valid_environment().thenReturn(False).thenReturn(False).thenReturn(True)
        when(time).sleep(ANY)

        sut.verify_allowed_to_run(dummy_concurrency_checker)

        verify(dummy_concurrency_checker, times=3).is_valid_environment()
        verify(time, times=2).sleep(300)

    def test_still_active(self):
        expected_result = False
        dummy_concurrency_checker = mock()
        when(dummy_concurrency_checker).is_valid_environment().thenReturn(expected_result)

        result = sut.still_active(dummy_concurrency_checker)

        self.assertIsNotNone(result)
        self.assertEqual(expected_result, result)
        verify(dummy_concurrency_checker, times=1).is_valid_environment()
