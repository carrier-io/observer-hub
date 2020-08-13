import hashlib
import json
from datetime import datetime

import docker
from apscheduler.schedulers.background import BackgroundScheduler
from mitmproxy import http
from mitmproxy import proxy, options
from mitmproxy.tools.dump import DumpMaster

from browser_hub.constants import TIMEOUT, SCHEDULER_INTERVAL, SELENIUM_PORT, VIDEO_PORT, SCREEN_RESOLUTION
from browser_hub.docker_client import DockerClient
from browser_hub.integrations.galloper import notify_on_test_start, notify_on_command_end, get_thresholds
from browser_hub.processors.request_processors import process_request
from browser_hub.processors.results_processor import generate_html_report, \
    process_results_for_test, process_results_for_page
from browser_hub.util import wait_for_agent, get_desired_capabilities, read_config, wait_for_hub, is_actionable, logger
from browser_hub.video import stop_recording, start_video_recording

docker_client = DockerClient(docker.from_env())
scheduler = BackgroundScheduler()
config = read_config()

mapping = {}
execution_results = []
locators = {}
commands = {}


def container_inspector_job():
    logger.info(f'There are {len(mapping.keys())} containers running...')
    deleted = []
    for k, v in mapping.items():
        if 'lastly_used' not in v.keys():
            continue
        lastly_used = datetime.strptime(v['lastly_used'], '%Y-%m-%d %H:%M:%S.%f')
        now = datetime.now()
        diff = (now - lastly_used).seconds
        container_id = v['container_id']

        logger.info(f"Container {container_id} was lastly used {diff} seconds ago")

        if diff >= TIMEOUT:
            generate_report(v)
            logger.info(f"Container {container_id} usage time exceeded timeout!")
            docker_client.get_container(container_id).remove(force=True)
            logger.info(f"Container {container_id} was deleted!")
            deleted.append(k)
            locators.pop(v['session_id'], None)
            commands.pop(v['session_id'], None)

    for d in deleted:
        mapping.pop(d, None)


def generate_report(args):
    report_id = args['report_id']
    browser_name = args['desired_capabilities']['browserName']
    version = args['desired_capabilities']['version']

    test_name = f"{browser_name}_{version}"

    process_results_for_test(report_id, test_name, execution_results, [], False)
    execution_results.clear()


class Interceptor:
    def __init__(self):
        pass

    def request(self, flow):
        original_request = flow.request

        path_components = list(original_request.path_components)
        host = None
        host_hash = None

        # maybe move to response method
        if original_request.method != "GET" and \
                original_request.method != "DELETE" and \
                original_request.path != '/wd/hub/session':
            content = json.loads(original_request.content.decode('utf-8'))
            session_id = path_components[3][32:]
            command = {}
            if original_request.path.endswith("/url"):
                command = {
                    "command": "open",
                    "target": content['url'],
                    "value": ""
                }
            if original_request.path.endswith("/click"):
                locator = locators[session_id][path_components[5]]
                command = {
                    "command": "click",
                    "target": locator['value'],
                    "value": ""
                }

            if command:
                if session_id in commands.keys():
                    commands[session_id].append(command)
                else:
                    commands[session_id] = [command]

        if "element" in original_request.path and is_actionable(original_request.path):
            session_id = path_components[3]
            host_hash = session_id[0:32]
            host = mapping[host_hash]['host']
            start_time = mapping[host_hash]['start_time']
            session_id = session_id[32:]

            results = process_request(original_request, host, session_id, start_time, locators,
                                      commands[session_id][:-1])

            video_host = mapping[host_hash]['video']
            video_folder, video_path = stop_recording(video_host)
            results.video_folder = video_folder
            results.video_path = video_path

            if results.results:
                report_id = mapping[host_hash]["report_id"]
                thresholds = mapping[host_hash]['thresholds']

                process_results_for_page(report_id, results, thresholds)
                execution_results.append(results)

            start_time = start_video_recording(video_host)
            mapping[host_hash]['start_time'] = start_time

        if "/wd/hub/session" in original_request.path and original_request.method == "DELETE":
            session_id = path_components[3]
            host_hash = session_id[0:32]
            host = mapping[host_hash]['host']
            start_time = mapping[host_hash]['start_time']
            session_id = session_id[32:]

            results = process_request(original_request, host, session_id, start_time, locators, commands[session_id])

            video_host = mapping[host_hash]['video']
            video_folder, video_path = stop_recording(video_host)
            results.video_folder = video_folder
            results.video_path = video_path

            if results.results:
                report_id = mapping[host_hash]["report_id"]
                thresholds = mapping[host_hash]['thresholds']

                process_results_for_page(report_id, results, thresholds)
                execution_results.append(results)

        if original_request.path == "/wd/hub/session":
            desired_capabilities = get_desired_capabilities(original_request)
            browser_name = desired_capabilities['browserName']
            version = desired_capabilities['version']

            container_id, selenium_port, video_port = start_container(browser_name, version)

            host = f"localhost:{selenium_port}"
            host_hash = hashlib.md5(host.encode('utf-8')).hexdigest()
            report_id, test_name = notify_on_test_start(desired_capabilities)
            thresholds = get_thresholds(test_name)

            mapping[host_hash] = {
                "host": f"localhost:{selenium_port}",
                "container_id": container_id,
                "video": f"localhost:{video_port}",
                "report_id": report_id,
                "desired_capabilities": desired_capabilities,
                "thresholds": thresholds
            }

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

            video_host = mapping[host_hash]["video"]
            start_time = start_video_recording(video_host)
            mapping[host_hash]['start_time'] = start_time
            mapping[host_hash]['session_id'] = session_id

        if flow.request.path.endswith("element"):
            session_id = flow.request.path_components[3]
            content = json.loads(response.decode('utf-8'))
            element_id = [*content['value'].values()][0]

            locator = json.loads(flow.request.content.decode('utf-8'))
            if session_id in locators.keys():
                locators[session_id][element_id] = locator
            else:
                locators[session_id] = {element_id: locator}

        flow.response = http.HTTPResponse.make(
            flow.response.status_code,
            response,
            flow.response.headers.fields
        )


def start_container(browser_name, version):
    container_config = get_container_configuration(browser_name, version)
    container_image = container_config['image']

    logger.info(f"Starting container {container_image} ...")
    container = docker_client.run(
        container_image,
        detach=True,
        ports={f"{SELENIUM_PORT}": None, f"{VIDEO_PORT}": None},
        environment=[f"RESOLUTION={SCREEN_RESOLUTION}"],
        privileged=True
    )
    selenium_port = docker_client.port(container.short_id, SELENIUM_PORT)
    video_port = docker_client.port(container.short_id, VIDEO_PORT)
    wait_for_hub("localhost", selenium_port)
    wait_for_agent("localhost", video_port)

    logger.info(f'Container has been {container.id} started')
    return container.short_id, selenium_port, video_port


def get_container_configuration(browser_name, version):
    cfg = config[browser_name]
    if not version:
        version = cfg['default']

    return cfg['versions'][version]


def start_proxy():
    opts = options.Options(listen_host='0.0.0.0',
                           listen_port=4444,
                           mode="transparent")
    pconf = proxy.config.ProxyConfig(opts)
    m = DumpMaster(opts)
    m.server = proxy.server.ProxyServer(pconf)
    logger.info('Intercepting Proxy listening on 4444')

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
