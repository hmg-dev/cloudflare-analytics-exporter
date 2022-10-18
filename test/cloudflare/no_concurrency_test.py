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

import os
import requests
import unittest

from cloudflare.no_concurrency import NoConcurrency
from cloudflare import config
from mockito import when, mock, unstub, verify, ANY, verifyZeroInteractions


class NoConcurrencyTest(unittest.TestCase):
    def setUp(self) -> None:
        unittest.TestCase.setUp(self)
        self.sut = NoConcurrency()

    def tearDown(self) -> None:
        unittest.TestCase.tearDown(self)
        unstub()

    def test_is_valid_environment_for_disabled_check(self):
        config.check_for_concurrency = False
        when(os)
        when(requests)

        result = self.sut.is_valid_environment()

        self.assertIsNotNone(result)
        self.assertTrue(result)
        verifyZeroInteractions(os, requests)

    def test_is_valid_environment_for_check_ok(self):
        config.check_for_concurrency = True
        dummy_cluster = "cluster1"
        dummy_namespace = "namespace1"
        expected_url = f"{config.no_concurrency_uri}?cluster={dummy_cluster}&namespace={dummy_namespace}"
        response = mock({
            "status_code": 200, "text": "True"
        }, spec=requests.Response)

        when(os).getenv(self.sut.namespace_env_var).thenReturn(dummy_namespace)
        when(os).getenv(self.sut.cluster_env_var).thenReturn(dummy_cluster)
        when(requests).get(ANY(str)).thenReturn(response)

        result = self.sut.is_valid_environment()

        self.assertIsNotNone(result)
        self.assertTrue(result)
        verify(os, times=1).getenv(self.sut.cluster_env_var)
        verify(os, times=1).getenv(self.sut.namespace_env_var)
        verify(requests, times=1).get(expected_url)

    def test_is_valid_environment_for_check_ok_with_linebreak(self):
        config.check_for_concurrency = True
        dummy_cluster = "cluster1"
        dummy_namespace = "namespace1"
        expected_url = f"{config.no_concurrency_uri}?cluster={dummy_cluster}&namespace={dummy_namespace}"
        response = mock({
            "status_code": 200, "text": "True\n"
        }, spec=requests.Response)

        when(os).getenv(self.sut.namespace_env_var).thenReturn(dummy_namespace)
        when(os).getenv(self.sut.cluster_env_var).thenReturn(dummy_cluster)
        when(requests).get(ANY(str)).thenReturn(response)

        result = self.sut.is_valid_environment()

        self.assertIsNotNone(result)
        self.assertTrue(result)
        verify(os, times=1).getenv(self.sut.cluster_env_var)
        verify(os, times=1).getenv(self.sut.namespace_env_var)
        verify(requests, times=1).get(expected_url)

    def test_is_valid_environment_for_check_failed(self):
        config.check_for_concurrency = True
        dummy_cluster = "cluster_invalid"
        dummy_namespace = "namespace_invalid"
        expected_url = f"{config.no_concurrency_uri}?cluster={dummy_cluster}&namespace={dummy_namespace}"
        response = mock({
            "status_code": 200, "text": "False"
        }, spec=requests.Response)

        when(os).getenv(self.sut.namespace_env_var).thenReturn(dummy_namespace)
        when(os).getenv(self.sut.cluster_env_var).thenReturn(dummy_cluster)
        when(requests).get(ANY(str)).thenReturn(response)

        result = self.sut.is_valid_environment()

        self.assertIsNotNone(result)
        self.assertFalse(result)
        verify(os, times=1).getenv(self.sut.cluster_env_var)
        verify(os, times=1).getenv(self.sut.namespace_env_var)
        verify(requests, times=1).get(expected_url)

    def test_is_valid_environment_for_check_timeout(self):
        config.check_for_concurrency = True
        dummy_cluster = "cluster_invalid"
        dummy_namespace = "namespace_invalid"
        expected_url = f"{config.no_concurrency_uri}?cluster={dummy_cluster}&namespace={dummy_namespace}"

        when(os).getenv(self.sut.namespace_env_var).thenReturn(dummy_namespace)
        when(os).getenv(self.sut.cluster_env_var).thenReturn(dummy_cluster)
        when(requests).get(ANY(str)).thenRaise(requests.exceptions.Timeout("TEST TIMEOUT"))

        result = self.sut.is_valid_environment()

        self.assertIsNotNone(result)
        self.assertFalse(result)
        verify(os, times=1).getenv(self.sut.cluster_env_var)
        verify(os, times=1).getenv(self.sut.namespace_env_var)
        verify(requests, times=1).get(expected_url)
