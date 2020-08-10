import base64

import requests

from browser_hub.constants import check_ui_performance


class PerfAgent(object):

    def __init__(self, host, session_id):
        self.host = host
        self.session_id = session_id

    def __execute_script(self, script):
        content = {"script": script, "args": []}

        url = f'http://{self.host}/wd/hub/session/{self.session_id}/execute/sync'
        res = requests.post(url=url, json=content)
        return res.json()['value']

    def get_performance_timing(self):
        return self.__execute_script("return performance.timing")

    def page_title(self):
        res = requests.get(f'http://{self.host}/wd/hub/session/{self.session_id}/title')
        return res.json()['value']

    def get_dom_size(self):
        return self.__execute_script("return document.getElementsByTagName('*').length")

    def get_performance_metrics(self):
        return self.__execute_script(check_ui_performance)

    def get_performance_entities(self):
        return self.__execute_script("return performance.getEntriesByType('resource')")

    def take_screenshot(self, filename):
        res = requests.get(f'http://{self.host}/wd/hub/session/{self.session_id}/screenshot')
        encoded_data = res.json()['value']
        imgdata = base64.b64decode(encoded_data)
        with open(filename, 'wb') as f:
            f.write(imgdata)

        return filename
