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
import json
import os

from cloudflare import config
from elasticsearch import Elasticsearch, ApiError, helpers

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


class DataStore(object):

    def __init__(self):
        self.es = None
        self.es_password = os.getenv(config.es_pass_env)

    @staticmethod
    def read_resource_from_file(filename):
        with open(os.path.dirname(__file__) + f"/resources/{filename}", 'r') as f:
            resource = f.read()

        return resource

    def connect(self):
        self.es = Elasticsearch(
            f"https://{config.es_host}:{config.es_port}",
            basic_auth=(config.es_user, self.es_password)
        )
        self._ensure_index()

        print(f"connected to elasticsearch: {self.es.info()}")

    def _ensure_index(self):
        if "false" == str(self.es.indices.exists(index=config.es_cf_index_pattern, allow_no_indices=False)).lower():
            print("index not found - commencing setup...")
            ilm_policy = json.loads(self.read_resource_from_file("ilm-policy.json"))
            index_template = json.loads(self.read_resource_from_file("index-template.json"))
            self.es.ilm.put_lifecycle(name=config.es_cf_policy, policy=ilm_policy)
            self.es.indices.put_index_template(name=config.es_cf_index_template,
                                               index_patterns=[config.es_cf_index_pattern], template=index_template)
            self.es.indices.create(index=config.es_cf_initial_index, aliases={config.es_cf_index: {"is_write_index": True}})

    def find_latest_reference_datetime(self):
        latest_ref = None
        try:
            latest_doc = self.es.search(index=config.es_cf_index, size=1,
                                        query={"match_all": {}}, sort={"@timestamp": "desc"})
            if latest_doc.get("hits").get("total").get("value") > 0:
                latest_ref = datetime.datetime.strptime(
                    latest_doc.get("hits").get("hits")[0].get("_source").get("@timestamp"), DATETIME_FORMAT)
                if datetime.datetime.utcnow() - datetime.timedelta(seconds=608400) > latest_ref:
                    latest_ref = None
        except ApiError as e:
            print(f"unable to determine latest reference datetime: {e}")

        return latest_ref

    def store_document(self, doc):
        return self.es.index(index=config.es_cf_index, document=doc, require_alias=True)

    @staticmethod
    def _create_bulk_data(docs):
        for doc in docs:
            yield {
                "_index": config.es_cf_index,
                "_source": doc
            }

    def store_documents(self, docs):
        helpers.bulk(self.es, self._create_bulk_data(docs))
