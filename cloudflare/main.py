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
import time
import traceback

from cloudflare import analytics_api
from cloudflare import datastore
from cloudflare import no_concurrency


dt_helper = analytics_api.dt_helper
ds = datastore.DataStore()


def run_fetch_and_push(reference_dt, storage):
    start_datetime = dt_helper.time_floor(reference_dt, datetime.timedelta(seconds=60))

    try:
        data = analytics_api.fetch_cloudflare_analytics(start_datetime)
        print(f"{datetime.datetime.now()} - indexing {len(data)} documents...")
        storage.store_documents(docs=data)

        reference_dt = dt_helper.determine_interval_datetime(start_datetime)
        if dt_helper.is_need_catchup(reference_dt):
            print(f"{datetime.datetime.now()} - Still not up2date - use short wait-interval")
            time.sleep(5)
        else:
            print(f"{datetime.datetime.now()} - up2date - going to sleep a while")
            time.sleep(60)
    except Exception as e:
        print(f"Error processing data: {e}")
        print(f"{e}\nCaused by: {traceback.format_exc()}")

    return reference_dt


def still_active(concurrency_checker):
    return concurrency_checker.is_valid_environment()


# method will block and re-check regularly instead of exiting the app.
# this is to prevent kubernetes to restart the POD over and over again!
def verify_allowed_to_run(concurrency_checker):
    print(f"{datetime.datetime.now()} - Check if instance is allowed to run...")
    while not concurrency_checker.is_valid_environment():
        print(f"{datetime.datetime.now()} - NOT RUNNING - local instance not matching desired active environment")
        time.sleep(300)
    print(f"{datetime.datetime.now()} - GOT GREEN LIGHT (matching active environment) - proceed with startup...")


def main(storage):
    print("START cloudflare-analytics-exporter")
    concurrency_checker = no_concurrency.NoConcurrency()
    verify_allowed_to_run(concurrency_checker)

    storage.connect()
    ref_datetime = storage.find_latest_reference_datetime()
    if ref_datetime is None:
        ref_datetime = dt_helper.current_ref_datetime()

    while still_active(concurrency_checker):
        ref_datetime = run_fetch_and_push(ref_datetime, storage)


if __name__ == '__main__':
    main(ds)
