from datetime import timedelta
from uuid import uuid4

from observer_hub.constants import REPORTS_BUCKET, REPORT_PATH, TIMEOUT
from observer_hub.integrations.galloper_api_client import create_galloper_report, send_gelloper_report_results, \
    upload_artifacts, \
    finalize_galloper_report
from observer_hub.models.exporters import GalloperExporter
from observer_hub.util import logger, current_time


def notify_on_test_start(galloper_url, galloper_project_id, galloper_token, desired_capabilities):
    browser_name = desired_capabilities['browserName']
    version = desired_capabilities['version']

    if version:
        version = f'_{version}'

    test_name = desired_capabilities.get("scenario_name", f"{browser_name}{version}")
    base_url = desired_capabilities.get('base_url', "")
    loops = desired_capabilities.get('loops', 1)
    aggregation = desired_capabilities.get('aggregation', 'max')
    report_uid = desired_capabilities.get('report_uid', str(uuid4()))
    env = desired_capabilities.get('venv', '')
    tz = desired_capabilities.get('tz', 'UTC')
    version = desired_capabilities.get('version', '')
    job_name = desired_capabilities.get('job_name', '')

    data = {
        "report_id": report_uid,
        "test_name": job_name,
        "base_url": base_url,
        "browser_name": browser_name,
        "browser_version": version,
        "env": env,
        "loops": loops,
        "aggregation": aggregation,
        "time": current_time(tz).strftime('%Y-%m-%d %H:%M:%S')
    }

    create_galloper_report(galloper_url, galloper_project_id, galloper_token, data)

    return report_uid, job_name


def notify_on_test_end(galloper_url, galloper_project_id, galloper_token, report_id, total_thresholds, exception,
                       junit_report_name,
                       junit_report_bucket, tz):
    logger.info(f"About to notify on test end for report {report_id}")

    time = current_time(tz) - timedelta(seconds=TIMEOUT)

    data = {
        "report_id": report_id,
        "time": time.strftime('%Y-%m-%d %H:%M:%S'),
        "status": "Finished",
        "thresholds_total": total_thresholds.get("total", 0),
        "thresholds_failed": total_thresholds.get("failed", 0)
    }

    if exception:
        data["exception"] = str(exception)

    finalize_galloper_report(galloper_url, galloper_project_id, galloper_token, data)

    if junit_report_name:
        logger.info(f"About to upload junit report to {junit_report_bucket}")
        upload_artifacts(galloper_url, galloper_project_id, galloper_token, junit_report_bucket,
                         f"{REPORT_PATH}/junit/{junit_report_name}",
                         junit_report_name)


def notify_on_command_end(galloper_url, galloper_project_id, galloper_token, report_id, report, minio_package,
                          execution_result, thresholds, session_id):
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
        "locators": execution_result.commands,
        "session_id": session_id
    }

    send_gelloper_report_results(galloper_url, galloper_project_id, galloper_token, report_id, data)

    upload_artifacts(galloper_url, galloper_project_id, galloper_token, REPORTS_BUCKET, report.path, report.file_name)
    upload_artifacts(galloper_url, galloper_project_id, galloper_token, REPORTS_BUCKET,
                     minio_package.path, minio_package.file_name)
