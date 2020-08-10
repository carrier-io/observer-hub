import json
from time import sleep
from deepdiff import DeepDiff
import requests

from browser_hub.constants import CONFIG_PATH


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
