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

cf_api_endpoint = "https://api.cloudflare.com/client/v4/graphql"
cf_api_token_env = "CF_API_TOKEN"
cf_api_user = "_REPLACEME_"

cf_fetch_delay_in_seconds = 300
cf_data_interval_in_seconds = 61

es_host = "_REPLACEME_"
es_port = 9200
es_user = "_REPLACEME_"
es_pass_env = "ES_PASSWD"

# Attention: when changing the index-name, it must also be changed in "resources/index-template.json"!!
es_cf_index = "cf-analytics"
es_cf_initial_index = f"{es_cf_index}-000001"
es_cf_policy = "cf-analytics-policy"
es_cf_index_template = "cf-analytics"
es_cf_index_pattern = "cf-analytics*"

check_for_concurrency = False
no_concurrency_uri = "https://cfae-concurrency.local/"

# Don't forget to replace/fill in the zone-mapping:
zones = {
    "00000000000000000000000000000000": "domain.tld",
    "11111111111111111111111111111111": "example.tld"
}
