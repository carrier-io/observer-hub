from traceback import format_exc

import requests
from observer_hub.util import logger


def get_headers(token):
    if token:
        return {'Authorization': f"Bearer {token}"}
    logger.warning("=====> Auth TOKEN is not set!")
    return None


def create_galloper_report(galloper_url, galloper_project_id, galloper_token, data):
    try:
        requests.post(f"{galloper_url}/api/v1/observer/{galloper_project_id}", json=data,
                      headers=get_headers(galloper_token))
    except Exception:
        logger.error(format_exc())


def finalize_galloper_report(galloper_url, galloper_project_id, galloper_token, data):
    try:
        requests.put(f"{galloper_url}/api/v1/observer/{galloper_project_id}", json=data,
                     headers=get_headers(galloper_token))
    except Exception:
        logger.error(format_exc())


def get_thresholds(galloper_url, galloper_project_id, galloper_token, test_name, env):
    logger.info(f"Get thresholds for: {test_name} {env}")
    res = None
    try:
        res = requests.get(
            f"{galloper_url}/api/v1/thresholds/{galloper_project_id}/ui?name={test_name}&environment={env}&order=asc",
            headers=get_headers(galloper_token))
    except Exception:
        logger.error(format_exc())

    if not res or res.status_code != 200:
        return {}

    try:
        return res.json()
    except ValueError:
        return {}


def send_gelloper_report_results(galloper_url, galloper_project_id, galloper_token, report_id, data):
    try:
        requests.post(f"{galloper_url}/api/v1/observer/{galloper_project_id}/{report_id}", json=data,
                      headers=get_headers(galloper_token))
    except Exception:
        logger.error(format_exc())


def upload_artifacts(galloper_url, galloper_project_id, galloper_token, bucket_name, file_path, file_name):
    file = {'file': open(file_path, 'rb')}

    try:
        requests.post(f"{galloper_url}/api/v1/artifacts/{galloper_project_id}/{bucket_name}/{file_name}",
                      files=file,
                      headers=get_headers(galloper_token))
    except Exception:
        logger.error(format_exc())


def send_report_locators(galloper_url, galloper_token, project_id: int, report_id: int, exception):
    try:
        requests.put(f"{galloper_url}/api/v1/observer/{project_id}/{report_id}",
                     json={"exception": exception, "status": ""},
                     headers=get_headers(galloper_token))
    except Exception:
        logger.error(format_exc())
