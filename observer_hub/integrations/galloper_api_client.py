import requests
from observer_hub.constants import GALLOPER_URL, GALLOPER_PROJECT_ID, TOKEN, ENV
from observer_hub.util import logger
from traceback import format_exc


def get_headers():
    if TOKEN:
        return {'Authorization': f"Bearer {TOKEN}"}
    logger.warning("=====> Auth TOKEN is not set!")
    return None


def create_galloper_report(data):
    try:
        requests.post(f"{GALLOPER_URL}/api/v1/observer/{GALLOPER_PROJECT_ID}", json=data,
                      headers=get_headers())
    except Exception:
        logger.error(format_exc())


def finalize_galloper_report(data):
    try:
        requests.put(f"{GALLOPER_URL}/api/v1/observer/{GALLOPER_PROJECT_ID}", json=data,
                     headers=get_headers())
    except Exception:
        logger.error(format_exc())


def get_thresholds(test_name):
    logger.info(f"Get thresholds for: {test_name} {ENV}")
    res = None
    try:
        res = requests.get(
            f"{GALLOPER_URL}/api/v1/thresholds/{GALLOPER_PROJECT_ID}/ui?name={test_name}&environment={ENV}&order=asc",
            headers=get_headers())
    except Exception:
        logger.error(format_exc())

    if not res or res.status_code != 200:
        return {}

    try:
        return res.json()
    except ValueError:
        return {}


def send_gelloper_report_results(report_id, data):
    try:
        requests.post(f"{GALLOPER_URL}/api/v1/observer/{GALLOPER_PROJECT_ID}/{report_id}", json=data,
                            headers=get_headers())
    except Exception:
        logger.error(format_exc())


def upload_artifacts(bucket_name, file_path, file_name):
    file = {'file': open(file_path, 'rb')}

    try:
        requests.post(f"{GALLOPER_URL}/api/v1/artifacts/{GALLOPER_PROJECT_ID}/{bucket_name}/{file_name}",
                      files=file,
                      headers=get_headers())
    except Exception:
        logger.error(format_exc())


def send_report_locators(project_id: int, report_id: int, exception):
    try:
        requests.put(f"{GALLOPER_URL}/api/v1/observer/{project_id}/{report_id}",
                     json={"exception": exception, "status": ""},
                     headers=get_headers())
    except Exception:
        logger.error(format_exc())
