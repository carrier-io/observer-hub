import json
from time import sleep

import requests


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
