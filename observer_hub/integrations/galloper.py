from datetime import datetime, timedelta
from uuid import uuid4

import pytz
import requests

from galloper_api_client import create_galloper_report, send_gelloper_report_results, upload_artifacts, \
    finalize_galloper_report
from observer_hub.constants import GALLOPER_URL, GALLOPER_PROJECT_ID, ENV, \
    REPORTS_BUCKET, REPORT_PATH, TZ, TIMEOUT
from observer_hub.models.exporters import GalloperExporter
from observer_hub.util import logger


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

    create_galloper_report(data)

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

    finalize_galloper_report(data)

    if junit_report_name:
        logger.info(f"About to upload junit report to {junit_report_bucket}")
        upload_artifacts(junit_report_bucket, f"{REPORT_PATH}/junit/{junit_report_name}", junit_report_name)


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

    send_gelloper_report_results(report_id, data)

    upload_artifacts(REPORTS_BUCKET, report.path, report.file_name)
