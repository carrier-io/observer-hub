import hashlib
import json
from datetime import datetime

import docker
from apscheduler.schedulers.background import BackgroundScheduler
from mitmproxy import http
from mitmproxy import proxy, options
from mitmproxy.tools.dump import DumpMaster

from browser_hub.docker_client import DockerClient
from browser_hub.util import wait_for_agent, get_desired_capabilities
from constants import TIMEOUT, SCHEDULER_INTERVAL, SELENIUM_PORT, VIDEO_PORT, SCREEN_RESOLUTION, CONTAINERS

docker_client = DockerClient(docker.from_env())
scheduler = BackgroundScheduler()

mapping = {}


def container_inspector_job():
    print(f'There are {len(mapping.keys())} containers running...')
    deleted = []
    for k, v in mapping.items():
        if 'lastly_used' not in v.keys():
            continue
        lastly_used = datetime.strptime(v['lastly_used'], '%Y-%m-%d %H:%M:%S.%f')
        now = datetime.now()
        diff = (now - lastly_used).seconds
        container_id = v['container_id']

        print(f"Container {container_id} was lastly used {diff} seconds ago")

        if diff > TIMEOUT:
            docker_client.get_container(container_id).remove(force=True)
            deleted.append(k)

    for d in deleted:
        mapping.pop(d, None)


class Interceptor:
    def __init__(self):
        pass

    def request(self, flow):
        original_request = flow.request
        print(original_request.path)

        path_components = list(original_request.path_components)

        host = None
        host_hash = None

        if original_request.path == "/wd/hub/session":
            desired_capabilities = get_desired_capabilities(original_request)
            browser_name = desired_capabilities['browserName']

            container_id, selenium_port, video_port = start_container(browser_name)

            host = f"localhost:{selenium_port}"
            host_hash = hashlib.md5(host.encode('utf-8')).hexdigest()
            mapping[host_hash] = {
                "host": f"localhost:{selenium_port}",
                "container_id": container_id,
                "video": f"localhost:{video_port}"
            }

        if original_request.path.startswith("/record/"):
            session_id = original_request.query.fields[0][1]
            host_hash = session_id[0:32]
            host = mapping[host_hash]['video']

        if len(path_components) > 3:
            session_id = path_components[3]
            host_hash = session_id[0:32]
            host = mapping[host_hash]['host']
            path_components[3] = session_id[32:]

        url = f"{original_request.scheme}://{host}/{'/'.join(path_components)}"

        flow.request = http.HTTPRequest.make(
            method=original_request.method,
            url=url,
            content=original_request.content,
            headers=original_request.headers.fields
        )

        mapping[host_hash]["lastly_used"] = str(datetime.now())

    def response(self, flow):
        response = flow.response.content

        if flow.request.path == "/wd/hub/session":
            host_hash = hashlib.md5(f"localhost:{flow.request.port}".encode('utf-8')).hexdigest()
            content = json.loads(response.decode('utf-8'))

            session_id = content['value']['sessionId']
            content['value']['sessionId'] = host_hash + session_id
            response = json.dumps(content).encode('utf-8')

        flow.response = http.HTTPResponse.make(
            flow.response.status_code,
            response,
            flow.response.headers.fields
        )


def start_container(browser_name):
    container_name = CONTAINERS[browser_name]
    print(f"Starting container {container_name} ...")
    container = docker_client.run(
        container_name,
        detach=True,
        ports={f"{SELENIUM_PORT}": None, f"{VIDEO_PORT}": None},
        environment=[f"RESOLUTION={SCREEN_RESOLUTION}"]
    )
    selenium_port = docker_client.port(container.short_id, SELENIUM_PORT)
    video_port = docker_client.port(container.short_id, VIDEO_PORT)
    wait_for_agent("localhost", video_port)

    print(f'Container has been {container.id} started')
    return container.short_id, selenium_port, video_port


def start_proxy():
    opts = options.Options(listen_host='0.0.0.0',
                           listen_port=4444,
                           mode="transparent")
    pconf = proxy.config.ProxyConfig(opts)
    m = DumpMaster(opts)
    m.server = proxy.server.ProxyServer(pconf)
    print('Intercepting Proxy listening on 4444')

    m.addons.add(Interceptor())
    try:
        m.run()
    except KeyboardInterrupt:
        m.shutdown()


def main():
    scheduler.add_job(container_inspector_job, 'interval', seconds=SCHEDULER_INTERVAL)
    scheduler.start()
    start_proxy()


if __name__ == '__main__':
    main()
