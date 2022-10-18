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

from cloudflare import config


class DateTimeHelper(object):

    def __init__(self):
        self.CF_FETCH_DELAY_IN_SECONDS = config.cf_fetch_delay_in_seconds
        self.CF_DATA_INTERVAL_IN_SECONDS = config.cf_data_interval_in_seconds

    @staticmethod
    def time_mod(time, delta, epoch=None):
        if epoch is None:
            epoch = datetime.datetime(1970, 1, 1, tzinfo=time.tzinfo)
        return (time - epoch) % delta

    def time_floor(self, time, delta, epoch=None):
        mod = self.time_mod(time, delta, epoch)
        return time - mod

    def current_ref_datetime(self):
        return DateTimeHelper._utcnow() - datetime.timedelta(seconds=self.CF_FETCH_DELAY_IN_SECONDS)

    def determine_interval_datetime(self, reference_datetime):
        return reference_datetime + datetime.timedelta(seconds=self.CF_DATA_INTERVAL_IN_SECONDS)

    def is_need_catchup(self, ref_datetime):
        if self.determine_interval_datetime(ref_datetime) < self.current_ref_datetime():
            return True

        return False

    @staticmethod
    def format_datetime(dt):
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def _utcnow():
        return datetime.datetime.utcnow()
