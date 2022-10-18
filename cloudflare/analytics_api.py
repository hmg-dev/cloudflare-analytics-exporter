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
import os
import gql

import gql.transport.requests as gql_transport
from cloudflare import config
from cloudflare.datetime_helper import DateTimeHelper


dt_helper = DateTimeHelper()


def read_gql_query_from_file(filename):
    with open(os.path.dirname(__file__) + f"/templates/{filename}", 'r') as f:
        gql_query = f.read()

    return gql_query


def _create_doc_internal(zone_tag, timestamp, data_type, data_key, uniques=0, bytes=0, cached_bytes=0,
                         cached_requests=0, encrypted_bytes=0, encrypted_requests=0, page_views=0, requests=0):
    doc = {
        "dataType": data_type,
        "dataKey": data_key,
        "zoneTag": zone_tag,
        "zoneName": config.zones.get(zone_tag),
        "@timestamp": timestamp,
        "uniques": uniques,
        "bytes": bytes,
        "cachedBytes": cached_bytes,
        "cachedRequests": cached_requests,
        "encryptedBytes": encrypted_bytes,
        "encryptedRequests": encrypted_requests,
        "pageViews": page_views,
        "requests": requests
    }
    return doc


def create_doc_base(zone_tag, data_group, timestamp):
    sums = data_group.get("sum")
    return _create_doc_internal(zone_tag, timestamp, "base", "base", uniques=data_group.get("uniq").get("uniques"),
                                bytes=sums.get("bytes"), cached_bytes=sums.get("cachedBytes"),
                                cached_requests=sums.get("cachedRequests"),
                                encrypted_bytes=sums.get("encryptedBytes"),
                                encrypted_requests=sums.get("encryptedRequests"), page_views=sums.get("pageViews"),
                                requests=sums.get("requests"))


def create_docs_responsestatus(zone_tag, data_group, timestamp):
    docs = []
    for entry in data_group.get("sum").get("responseStatusMap"):
        docs.append(_create_doc_internal(zone_tag, timestamp, "responseStatus", entry.get("edgeResponseStatus"),
                                         requests=entry.get("requests")))
    return docs


def create_docs_country(zone_tag, data_group, timestamp):
    docs = []
    for entry in data_group.get("sum").get("countryMap"):
        docs.append(_create_doc_internal(zone_tag, timestamp, "country", entry.get("clientCountryName"),
                                         requests=entry.get("requests"), bytes=entry.get("bytes")))
    return docs


def create_docs_sslversion(zone_tag, data_group, timestamp):
    docs = []
    for entry in data_group.get("sum").get("clientSSLMap"):
        docs.append(_create_doc_internal(zone_tag, timestamp, "sslVersion", entry.get("clientSSLProtocol"),
                                         requests=entry.get("requests")))
    return docs


def create_docs_browsers(zone_tag, data_group, timestamp):
    docs = []
    for entry in data_group.get("sum").get("browserMap"):
        docs.append(_create_doc_internal(zone_tag, timestamp, "browser", entry.get("uaBrowserFamily"),
                                         page_views=entry.get("pageViews")))
    return docs


def create_docs_contenttype(zone_tag, data_group, timestamp):
    docs = []
    for entry in data_group.get("sum").get("contentTypeMap"):
        docs.append(_create_doc_internal(zone_tag, timestamp, "contentType", entry.get("edgeResponseContentTypeName"),
                                         requests=entry.get("requests"), bytes=entry.get("bytes")))
    return docs


def normalize_data(result):
    docs = []
    for item in result.get("viewer").get("zones"):
        for data_group in item.get("httpRequests1mGroups"):
            zone_tag = item.get('zoneTag')
            timestamp = datetime.datetime.strptime(data_group.get("dimensions").get("datetime"), "%Y-%m-%dT%H:%M:%SZ")
            docs.append(create_doc_base(zone_tag, data_group, timestamp))
            docs.extend(create_docs_responsestatus(zone_tag, data_group, timestamp))
            docs.extend(create_docs_country(zone_tag, data_group, timestamp))
            docs.extend(create_docs_sslversion(zone_tag, data_group, timestamp))
            docs.extend(create_docs_browsers(zone_tag, data_group, timestamp))
            docs.extend(create_docs_contenttype(zone_tag, data_group, timestamp))

    return docs


def fetch_cloudflare_analytics(ref_datetime):
    cf_api_token = os.getenv(config.cf_api_token_env)
    cf_headers = {"X-AUTH-EMAIL": config.cf_api_user, "Authorization": f"Bearer {cf_api_token}"}
    transport = gql_transport.RequestsHTTPTransport(
        url=config.cf_api_endpoint, verify=True, retries=3, headers=cf_headers)

    client = gql.Client(transport=transport, fetch_schema_from_transport=False)
    query = gql.gql(read_gql_query_from_file(filename="zone-totals.graphql"))
    to_datetime = dt_helper.determine_interval_datetime(ref_datetime)
    parameters = {
        "limit": 9999,
        "mintime": dt_helper.format_datetime(ref_datetime),
        "maxtime": dt_helper.format_datetime(to_datetime),
        "zoneIDs": list(config.zones.keys())
    }

    print(f"{datetime.datetime.now()} - query cf-api using fetch-parameters: {parameters}")
    result = client.execute(query, variable_values=parameters)

    return normalize_data(result)
