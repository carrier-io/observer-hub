from uuid import uuid4
from arbiter import Arbiter, Task
from observer_hub.constants import (REPORTS_BUCKET, RABBIT_HOST, RABBIT_QUEUE_NAME,
                                    RABBIT_PORT, RABBIT_USER, RABBIT_PASSWORD)


def port_async_processing_task(galloper_url, galloper_project_id, galloper_token, results,
                               report_name, minio_package_name):
    browsertime_package = f"{results.results['info']['title']}_{uuid4()}.zip"
    params = dict(galloper_url=galloper_url,
                  project_id=galloper_project_id,
                  token=galloper_token,
                  bucket=REPORTS_BUCKET,
                  filename=browsertime_package,
                  url=results.results["info"].get("url"),
                  headers=results.results["info"].get("headers"),
                  minio_package_name=minio_package_name,
                  report_filename=report_name,
                  browser="chrome")
    if RABBIT_HOST:
        arbiter = Arbiter(host=RABBIT_HOST, port=RABBIT_PORT, user=RABBIT_USER, password=RABBIT_PASSWORD,
                          start_consumer=False)
        arbiter.apply(Task('browsertime', queue=RABBIT_QUEUE_NAME, task_kwargs=params))
    return browsertime_package
