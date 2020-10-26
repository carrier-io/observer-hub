from json import JSONDecodeError

import requests
from observer_hub.util import logger


def init_email_notification(galloper_url, galloper_project_id, galloper_token, report_id):
    if galloper_url and galloper_token and galloper_project_id:
        secrets_url = f"{galloper_url}/api/v1/secrets/{galloper_project_id}/"
        try:
            email_notification_id = requests.get(secrets_url + "email_notification_id",
                                                 headers={'Authorization': f'bearer {galloper_token}',
                                                          'Content-type': 'application/json'}
                                                 ).json()["secret"]
        except (AttributeError, JSONDecodeError):
            email_notification_id = ""

        if email_notification_id:
            task_url = f"{galloper_url}/api/v1/task/{galloper_project_id}/{email_notification_id}"

            event = {
                "notification_type": "ui",
                "test_id": "",
                "report_id": report_id
            }

            res = requests.post(task_url, json=event, headers={'Authorization': f'bearer {galloper_token}',
                                                               'Content-type': 'application/json'})
            logger.info(f"Email notification {res.text}")
