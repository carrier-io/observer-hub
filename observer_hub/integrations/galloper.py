from datetime import datetime, timedelta
from uuid import uuid4

import pytz
import requests

from observer_hub.constants import GALLOPER_URL, GALLOPER_PROJECT_ID, TOKEN, ENV, \
    REPORTS_BUCKET, REPORT_PATH, TZ, TIMEOUT
from observer_hub.models.exporters import GalloperExporter
from observer_hub.util import logger


def get_thresholds(test_name):
    logger.info(f"Get thresholds for: {test_name} {ENV}")
    res = requests.get(
        f"{GALLOPER_URL}/api/v1/thresholds/{GALLOPER_PROJECT_ID}/ui?name={test_name}&environment={ENV}&order=asc",
        headers=get_headers())

    if res.status_code != 200:
        raise Exception(f"Can not get thresholds, Reasons {res.reason}")

    return res.json()


def notify_on_test_start(desired_capabilities):
    browser_name = desired_capabilities['browserName']
    version = desired_capabilities['version']

    if version:
        version = f'_{version}'

    test_name = desired_capabilities.get("scenario_name", f"{browser_name}{version}")
    base_url = desired_capabilities.get('base_url', "")
    loops = desired_capabilities.get('loops', 1)
    aggregation = desired_capabilities.get('aggregation', 'max')
    report_uid = desired_capabilities.get('report_uid', str(uuid4()))

    data = {
        "report_id": report_uid,
        "test_name": test_name,
        "base_url": base_url,
        "browser_name": browser_name,
        "env": ENV,
        "loops": loops,
        "aggregation": aggregation,
        "time": datetime.now(tz=pytz.timezone(TZ)).strftime('%Y-%m-%d %H:%M:%S')
    }

    requests.post(f"{GALLOPER_URL}/api/v1/observer/{GALLOPER_PROJECT_ID}", json=data,
                  headers=get_headers())
    return report_uid, test_name


def notify_on_test_end(report_id, total_thresholds, exception, junit_report_name, junit_report_bucket):
    logger.info(f"About to notify on test end for report {report_id}")

    time = datetime.now(tz=pytz.timezone(TZ)) - timedelta(seconds=TIMEOUT)

    data = {
        "report_id": report_id,
        "time": time.strftime('%Y-%m-%d %H:%M:%S'),
        "thresholds_total": total_thresholds.get("total", 0),
        "thresholds_failed": total_thresholds.get("failed", 0)
    }

    if exception:
        data["exception"] = str(exception)

    res = requests.put(f"{GALLOPER_URL}/api/v1/observer/{GALLOPER_PROJECT_ID}", json=data,
                       headers=get_headers())
    if junit_report_name:
        logger.info(f"About to upload junit report to {junit_report_bucket}")
        upload_artifacts(junit_report_bucket, f"{REPORT_PATH}/junit/{junit_report_name}", junit_report_name)
    return res.json()


def get_headers():
    if TOKEN:
        return {'Authorization': f"Bearer {TOKEN}"}
    logger.warning("Auth TOKEN is not set!")
    return None


def send_report_locators(project_id: int, report_id: int, exception):
    requests.put(f"{GALLOPER_URL}/api/v1/observer/{project_id}/{report_id}",
                 json={"exception": exception, "status": ""},
                 headers=get_headers())


def upload_artifacts(bucket_name, file_path, file_name):
    file = {'file': open(file_path, 'rb')}

    res = requests.post(f"{GALLOPER_URL}/api/v1/artifacts/{GALLOPER_PROJECT_ID}/{bucket_name}/{file_name}",
                        files=file,
                        headers=get_headers())
    return res.json()


def notify_on_command_end(report_id, report, execution_result, thresholds):
    name = execution_result.results['info']['title']
    metrics = execution_result.results
    logger.info(f"About to notify on command end for report {report_id}")
    result = GalloperExporter(metrics).export()

    data = {
        "name": name,
        "type": execution_result.results_type,
        "identifier": execution_result.page_identifier,
        "metrics": result,
        "bucket_name": REPORTS_BUCKET,
        "file_name": report.file_name,
        "resolution": metrics['info']['windowSize'],
        "browser_version": metrics['info']['browser'],
        "thresholds_total": thresholds.get("total", 0),
        "thresholds_failed": thresholds.get("failed", 0),
        "locators": execution_result.commands
    }

    res = requests.post(f"{GALLOPER_URL}/api/v1/observer/{GALLOPER_PROJECT_ID}/{report_id}", json=data,
                        headers=get_headers())

    upload_artifacts(REPORTS_BUCKET, report.path, report.file_name)

    return res.json()["id"]
