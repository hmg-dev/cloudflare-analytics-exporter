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

from cloudflare import config


class NoConcurrency(object):

    def __init__(self):
        self.cluster_env_var = "LOCAL_CLUSTER"
        self.namespace_env_var = "LOCAL_NAMESPACE"

    @staticmethod
    def _equals_ignorecase(string, string2):
        if str(string).lower().strip() == str(string2).lower().strip():
            return True
        return False

    def is_valid_environment(self):
        if not config.check_for_concurrency:
            return True

        local_cluster = os.getenv(self.cluster_env_var)
        local_ns = os.getenv(self.namespace_env_var)
        url = f"{config.no_concurrency_uri}?cluster={local_cluster}&namespace={local_ns}"

        try:
            response = requests.get(url)
        except requests.exceptions.RequestException as e:
            print(f"ERROR validating environment: {e}")
            return False

        return self._equals_ignorecase(response.text, "True")
