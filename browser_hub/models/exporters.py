import abc
import json
import os
import re
import time
from datetime import datetime
from urllib.parse import urlparse

from influxdb import InfluxDBClient

from browser_hub.constants import EXPORTERS_PATH
import uuid


class Exporter(object):

    def __init__(self, raw_data):
        self.raw_data = raw_data

        resources = raw_data['performanceResources']
        perf_timing = raw_data['performancetiming']
        timing = raw_data['timing']

        self.requests = self.count_request_number(resources)
        self.domains = self.count_unique_domain_number(resources)
        self.total_load_time = perf_timing['loadEventEnd'] - perf_timing['navigationStart']
        self.speed_index = timing['speedIndex']
        self.time_to_first_byte = perf_timing['responseStart'] - perf_timing['navigationStart']
        self.time_to_first_paint = timing['firstPaint']
        self.dom_content_loading = perf_timing['domContentLoadedEventStart'] - perf_timing['domLoading']
        self.dom_processing = perf_timing['domComplete'] - perf_timing['domLoading']

    def count_request_number(self, resources):
        return list(filter(
            lambda x: not re.match(r'/http[s]?:\/\/(micmro|nurun).github.io\/performance-bookmarklet\/.*/', x['name']),
            resources))

    def count_unique_domain_number(self, resources):
        result = set()
        for e in resources:
            url = urlparse(e['name'])
            result.add(url.netloc)
        return result

    @abc.abstractmethod
    def export(self):
        pass


class TelegraphJsonExporter(Exporter):

    def __init__(self, raw_data):
        super().__init__(raw_data)

    def export(self):
        # https://github.com/influxdata/telegraf/tree/master/plugins/serializers/json

        result = {
            "fields": {
                "requests": len(self.requests),
                "domains": len(self.domains),
                "total": self.total_load_time,
                "speed_index": self.speed_index,
                "time_to_first_byte": self.time_to_first_byte,
                "time_to_first_paint": self.time_to_first_paint,
                "dom_content_loading": self.dom_content_loading,
                "dom_processing": self.dom_processing
            },
            "name": self.raw_data['info']['title'],
            "tags": {},
            "timestamp": time.time()
        }
        os.makedirs(EXPORTERS_PATH, exist_ok=True)
        with open(os.path.join(EXPORTERS_PATH, f'{uuid.uuid1()}.json'), 'w') as outfile:
            json.dump(result, outfile, indent=4)
        return json.dumps(result)


class InfluxExporter(Exporter):

    def __init__(self, raw_data):
        influx_host = os.getenv("INFLUX_HOST", "carrier-influx")
        influx_port = os.getenv("INFLUX_PORT", "8086")
        influx_db_name = os.getenv("INFLUX_DB", "perfui")

        self.client = InfluxDBClient(host=influx_host, port=influx_port)
        self.client.switch_database(influx_db_name)
        super().__init__(raw_data)

    def export(self):
        json_body = [{
            "measurement": "ui_performance",
            "tags": {
                "name": self.raw_data['info']['title']
            },
            "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "fields": {
                "requests": len(self.requests),
                "domains": len(self.domains),
                "total": self.total_load_time,
                "speed_index": self.speed_index,
                "time_to_first_byte": self.time_to_first_byte,
                "time_to_first_paint": self.time_to_first_paint,
                "dom_content_loading": self.dom_content_loading,
                "dom_processing": self.dom_processing
            }
        }]

        self.client.write_points(json_body)


class GalloperExporter(Exporter):

    def __init__(self, raw_data):
        super().__init__(raw_data)

    def export(self):
        return {
            "requests": len(self.requests),
            "domains": len(self.domains),
            "total": self.total_load_time,
            "speed_index": self.speed_index,
            "time_to_first_byte": self.time_to_first_byte,
            "time_to_first_paint": self.time_to_first_paint,
            "dom_content_loading": self.dom_content_loading,
            "dom_processing": self.dom_processing
        }


class JsonExporter(Exporter):

    def __init__(self, raw_data):
        super().__init__(raw_data)

    def export(self):
        return {
            "measurement": "ui_performance",
            "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "fields": {
                "requests": len(self.requests),
                "domains": len(self.domains),
                "total": self.total_load_time,
                "speed_index": self.speed_index,
                "time_to_first_byte": self.time_to_first_byte,
                "time_to_first_paint": self.time_to_first_paint,
                "dom_content_loading": self.dom_content_loading,
                "dom_processing": self.dom_processing
            }
        }


class Exporter(object):

    def __init__(self, formats):
        self.formats = formats

    def export(self, data):
        if "telegraph" in self.formats:
            TelegraphJsonExporter(data).export()
        if "influx" in self.formats:
            InfluxExporter(data).export()

    def to_json(self, data):
        return JsonExporter(data).export()['fields']
