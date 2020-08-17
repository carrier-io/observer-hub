import hashlib
import json
import logging
import math
import os
from shutil import rmtree
from time import sleep
from deepdiff import DeepDiff
import requests

from observer_hub.constants import CONFIG_PATH

logger = logging.getLogger('Observer hub')

handler = logging.StreamHandler()
formatter = logging.Formatter('[%(name)s] - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def wait_for_agent(host, port):
    for _ in range(120):
        try:
            if requests.get(f'http://{host}:{port}').content == b'OK':
                break
        except:
            pass
        sleep(0.1)


def wait_for_hub(host, port):
    for _ in range(120):
        try:
            if requests.get(f'http://{host}:{port}/wd/hub/status').status_code == 200:
                break
        except:
            pass
        sleep(0.1)


def get_desired_capabilities(original_request):
    content = json.loads(original_request.content.decode('utf-8'))
    return content['desiredCapabilities']


def read_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def is_actionable(command):
    return "/click" in command


def is_performance_entities_changed(old_entities, latest_entries):
    ddiff = DeepDiff(old_entities, latest_entries, ignore_order=True)
    if not ddiff:
        return False

    if ddiff['iterable_item_added'] or ddiff['iterable_item_removed']:
        return True

    return False


def is_dom_changed(old_dom, new_dom):
    return old_dom != new_dom


def filter_thresholds_for(name, arr):
    test_scope = [x for x in arr if x['scope'] == name]
    every_scope = [x for x in arr if x['scope'] == 'every']
    return list({x['target']: x for x in every_scope + test_scope}.values())


def percentile(data, percentile):
    size = len(data)
    return sorted(data)[int(math.ceil((size * percentile) / 100)) - 1]


def is_values_match(actual, comparison, expected):
    if comparison == 'gte':
        return actual >= expected
    elif comparison == 'lte':
        return actual <= expected
    elif comparison == 'gt':
        return actual > expected
    elif comparison == 'lt':
        return actual < expected
    elif comparison == 'eq':
        return actual == expected
    return False


def get_aggregated_value(aggregation, metrics):
    if aggregation == 'max':
        return max(metrics), metrics
    elif aggregation == 'min':
        return min(metrics), metrics
    elif aggregation == 'avg':
        return round(sum(metrics) / len(metrics), 2), metrics
    elif aggregation == 'pct95':
        return percentile(metrics, 95), metrics
    elif aggregation == 'pct50':
        return percentile(metrics, 50), metrics
    else:
        raise Exception(f"No such aggregation {aggregation}")


def flatten_list(l):
    return [item for sublist in l for item in sublist]


def closest(lst, val):
    return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - val))]


def clean_up_data(results):
    logger.info("Cleaning up generated report data...")
    for execution_result in results:
        rmtree(execution_result.video_folder, ignore_errors=True)
        os.remove(execution_result.screenshot_path)
        os.remove(execution_result.report.path)


def request_to_command(original_request, locators):
    content = json.loads(original_request.content.decode('utf-8'))
    session_id = original_request.path_components[3][32:]
    command = {}
    if original_request.path.endswith("/url"):
        command = {
            "command": "open",
            "target": content['url'],
            "value": ""
        }
    if original_request.path.endswith("/click"):
        locator = locators[session_id][original_request.path_components[5]]
        command = {
            "command": "click",
            "target": locator['value'],
            "value": ""
        }

    return session_id, command


def get_hash(data):
    return hashlib.md5(data.encode('utf-8')).hexdigest()
