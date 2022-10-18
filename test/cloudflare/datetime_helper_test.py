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

import datetime
import unittest

from mockito import when, unstub, verify
from cloudflare.datetime_helper import DateTimeHelper


class DateTimeHelperTest(unittest.TestCase):
    def setUp(self) -> None:
        unittest.TestCase.setUp(self)
        self.sut = DateTimeHelper()
        self.dummy_current_dt = datetime.datetime.strptime("2022-09-20T12:12:00", "%Y-%m-%dT%H:%M:%S")

    def tearDown(self) -> None:
        unittest.TestCase.tearDown(self)
        unstub()

    def test_current_ref_datetime(self):
        expected_result = self.dummy_current_dt - datetime.timedelta(seconds=self.sut.CF_FETCH_DELAY_IN_SECONDS)
        when(DateTimeHelper)._utcnow().thenReturn(self.dummy_current_dt)

        result = self.sut.current_ref_datetime()

        self.assertIsNotNone(result)
        self.assertEqual(expected_result, result)
        verify(DateTimeHelper, times=1)._utcnow()

    def test_determine_interval_datetime(self):
        expected_result = self.dummy_current_dt + datetime.timedelta(seconds=self.sut.CF_DATA_INTERVAL_IN_SECONDS)

        result = self.sut.determine_interval_datetime(self.dummy_current_dt)

        self.assertIsNotNone(result)
        self.assertEqual(expected_result, result)

    def test_time_floor(self):
        dummy_input = datetime.datetime.strptime("2022-09-20T12:12:12", "%Y-%m-%dT%H:%M:%S")
        expected_result = datetime.datetime.strptime("2022-09-20T12:12:00", "%Y-%m-%dT%H:%M:%S")
        expected_result2 = datetime.datetime.strptime("2022-09-20T12:00:00", "%Y-%m-%dT%H:%M:%S")

        result = self.sut.time_floor(dummy_input, datetime.timedelta(seconds=60))
        result2 = self.sut.time_floor(dummy_input, datetime.timedelta(minutes=60))

        self.assertIsNotNone(result)
        self.assertEqual(expected_result, result)
        self.assertIsNotNone(result2)
        self.assertEqual(expected_result2, result2)

    def test_format_datetime(self):
        expected_result = "2022-09-20T12:12:00Z"

        result = DateTimeHelper.format_datetime(self.dummy_current_dt)

        self.assertIsNotNone(result)
        self.assertEqual(expected_result, result)

    def test_is_need_catchup(self):
        dt_two_hours_earlier = datetime.datetime.strptime("2022-09-20T10:19:00", "%Y-%m-%dT%H:%M:%S")
        when(DateTimeHelper)._utcnow().thenReturn(self.dummy_current_dt)

        result = self.sut.is_need_catchup(dt_two_hours_earlier)

        self.assertTrue(result)
        verify(DateTimeHelper, times=1)._utcnow()

    def test_is_need_catchup_for_up2date_ref(self):
        up2date_dt = datetime.datetime.strptime("2022-09-20T12:11:00", "%Y-%m-%dT%H:%M:%S")
        when(DateTimeHelper)._utcnow().thenReturn(self.dummy_current_dt)

        result = self.sut.is_need_catchup(up2date_dt)

        self.assertFalse(result)
        verify(DateTimeHelper, times=1)._utcnow()
