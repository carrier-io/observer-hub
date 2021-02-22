import base64

import requests

from observer_hub.constants import check_ui_performance


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

    def get_current_url(self):
        res = requests.get(f'http://{self.host}/wd/hub/session/{self.session_id}/url')
        return res.json()['value']

    def take_screenshot(self, filename):
        res = requests.get(f'http://{self.host}/wd/hub/session/{self.session_id}/screenshot')
        encoded_data = res.json()['value']
        imgdata = base64.b64decode(encoded_data)
        with open(filename, 'wb') as f:
            f.write(imgdata)
        return filename

    def get_page_headers(self):
        script = """var req = new XMLHttpRequest();
req.open('GET', document.location, false);
req.send(null);
return req.getAllResponseHeaders().toLowerCase();"""
        headers = self.__execute_script(script)
        headers_json = dict()
        for line in headers.strip().split('\n'):
            line_arr = line.split(":")
            try:
                headers_json[line_arr[0].strip()] = line_arr[1].strip()
            except IndexError:
                continue
        return headers_json
