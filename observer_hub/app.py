import json
from datetime import datetime

import docker
from apscheduler.schedulers.background import BackgroundScheduler
from mitmproxy import http
from mitmproxy import proxy, options
from mitmproxy.tools.dump import DumpMaster

from observer_hub.constants import TIMEOUT, SCHEDULER_INTERVAL, SELENIUM_PORT, VIDEO_PORT, SCREEN_RESOLUTION, QUOTA, \
    VNC_PORT
from observer_hub.docker_client import DockerClient
from observer_hub.integrations.galloper import notify_on_test_start, get_thresholds
from observer_hub.models.collector import CommandsCollector, LocatorsCollector, ExecutionResultsCollector
from observer_hub.processors.request_processors import process_request
from observer_hub.processors.results_processor import process_results_for_page, process_results_for_test
from observer_hub.util import wait_for_agent, get_desired_capabilities, read_config, wait_for_hub, is_actionable, \
    logger, clean_up_data, request_to_command, get_hash
from observer_hub.video import stop_recording, start_video_recording
from observer_hub.wait import wait_for_page_to_load

docker_client = DockerClient(docker.from_env())
scheduler = BackgroundScheduler()
config = read_config()

mapping = {}
execution_results = ExecutionResultsCollector()
locators = LocatorsCollector()
commands = CommandsCollector()


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

        if diff >= TIMEOUT and v['session_id'] in execution_results.keys():
            results = execution_results[v['session_id']]

            junit_report_name = generate_report(results, v)
            logger.info(f"Container {container_id} usage time exceeded timeout!")
            docker_client.get_container(container_id).remove(force=True)
            logger.info(f"Container {container_id} was deleted!")

            deleted.append(k)
            locators.pop(v['session_id'])
            commands.pop(v['session_id'])
            clean_up_data(results, junit_report_name)

    for d in deleted:
        mapping.pop(d, None)


def generate_report(results, args):
    report_id = args['report_id']
    browser_name = args['desired_capabilities']['browserName']
    version = args['desired_capabilities']['version']
    junit_report = args['junit_report']
    thresholds = args['thresholds']
    junit_report_bucket = args['junit_report_bucket']

    test_name = f"{browser_name}_{version}"
    _, junit_report_name = process_results_for_test(report_id, test_name, results, thresholds, junit_report, junit_report_bucket)
    return junit_report_name


class Interceptor:
    def __init__(self):
        pass

    def process(self, original_request, commands_full=False):
        session_id = original_request.path_components[3]
        host_hash = session_id[0:32]
        session_id = session_id[32:]
        host_info = mapping[host_hash]

        host = host_info['host']
        start_time = host_info['start_time']
        page_load_timeout = host_info['page_load_timeout']

        session_commands = commands[session_id][:-1]
        if commands_full:
            session_commands = commands[session_id]

        wait_for_page_to_load(page_load_timeout)

        results = process_request(original_request, host, session_id, start_time, locators[session_id],
                                  session_commands)

        video_host = host_info['video']
        video_folder, video_path = stop_recording(video_host)
        results.video_folder = video_folder
        results.video_path = video_path

        if results.results:
            report_id = host_info["report_id"]
            thresholds = host_info['thresholds']
            process_results_for_page(report_id, results, thresholds)
            execution_results.add(session_id, results)

        return host_hash, video_host

    def request(self, flow):
        original_request = flow.request

        path_components = list(original_request.path_components)
        host = None
        host_hash = None

        if flow.request.path == "/status" or flow.request.path == '/favicon.ico':
            content = {"quota": QUOTA, "active": len(mapping.keys())}
            response = json.dumps(content).encode('utf-8')
            flow.response = http.HTTPResponse.make(
                200,
                response
            )
            return

        if original_request.method != "GET" and \
                original_request.method != "DELETE" and \
                original_request.path != '/wd/hub/session':

            session_id, command = request_to_command(original_request, locators)

            if command:
                commands.add(session_id, command)

        if "element" in original_request.path and is_actionable(original_request.path):
            host_hash, video_host = self.process(original_request)

            start_time = start_video_recording(video_host)
            mapping[host_hash]['start_time'] = start_time

        if "/wd/hub/session" in original_request.path and original_request.method == "DELETE" \
                and len(original_request.path_components) == 4:
            self.process(original_request, commands_full=True)

        if original_request.path == "/wd/hub/session":
            desired_capabilities = get_desired_capabilities(original_request)
            browser_name = desired_capabilities['browserName']
            version = desired_capabilities.get('version', '')
            vnc = bool(desired_capabilities.get('vnc', False))
            page_load_timeout = int(desired_capabilities.get('page_load_timeout', 0))
            junit_report = desired_capabilities.get('junit_report', "")
            junit_report_bucket = desired_capabilities.get('junit_report_bucket', "")

            container_id, selenium_port, video_port = start_container(browser_name, version, vnc)

            host = f"localhost:{selenium_port}"
            host_hash = get_hash(host)
            report_id, test_name = notify_on_test_start(desired_capabilities)
            thresholds = get_thresholds(test_name)

            mapping[host_hash] = {
                "host": f"localhost:{selenium_port}",
                "container_id": container_id,
                "video": f"localhost:{video_port}",
                "report_id": report_id,
                "desired_capabilities": desired_capabilities,
                "thresholds": thresholds,
                'page_load_timeout': page_load_timeout,
                'junit_report': junit_report,
                'junit_report_bucket': junit_report_bucket
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
            host_hash = get_hash(f"localhost:{flow.request.port}")

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
            locators.save(session_id, element_id, locator)

        flow.response = http.HTTPResponse.make(
            flow.response.status_code,
            response,
            flow.response.headers.fields
        )


def start_container(browser_name, version, vnc):
    container_config = get_container_configuration(browser_name, version)
    container_image = container_config['image']
    env_vars = container_config.get('env', {})

    env = [f"RESOLUTION={SCREEN_RESOLUTION}"]
    for k, v in env_vars.items():
        env.append(f"{k}={v}")

    ports = {f"{SELENIUM_PORT}": None, f"{VIDEO_PORT}": None}
    if vnc:
        ports[VNC_PORT] = None

    logger.info(f"Starting container {container_image} ...")
    container = docker_client.run(
        container_image,
        detach=True,
        ports=ports,
        environment=env,
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
