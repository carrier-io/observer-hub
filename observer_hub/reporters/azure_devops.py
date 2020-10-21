import hashlib

from requests import post

from observer_hub.util import logger

PRIORITY_MAPPING = {"Critical": 1, "High": 1, "Medium": 2, "Low": 3, "Info": 4}


class AdoClient(object):

    def __init__(self, organization, project, personal_access_token,
                 team=None, issue_type="issue", rules="false", notify="false"):
        self.auth = ('', personal_access_token)
        self.team = f"{project}"
        if team:
            self.team = f"{project}\\{team}"

        self.url = f'https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/' \
                   f'${issue_type}?bypassRules={rules}&suppressNotifications={notify}&api-version=5.1'

        self.query_url = f'https://dev.azure.com/{organization}/{project}/_apis/wit/wiql?api-version=5.1'

    def get_issues(self, issue_hash=None):
        q = f"SELECT [System.Id] From WorkItems Where [System.Description] Contains \"{issue_hash}\""
        data = post(self.query_url, auth=self.auth, json={"query": q},
                    headers={'content-type': 'application/json'}).json()
        return data["workItems"]

    def create_issues(self, test_name, data):

        for d in data:
            if d['status'] == 'passed':
                continue

            issue_hash = hashlib.sha256(
                f"{d['scope']} {d['name']} {d['aggregation']} {d['raw_result'].page_identifier}".encode(
                    'utf-8')).hexdigest()

            if len(self.get_issues(issue_hash)) > 0:
                continue

            logger.info(f"=====> About to crate Azure DevOps issues")

            steps = []
            for i, cmd in enumerate(d['raw_result'].commands, 1):
                command = cmd['command']
                value = cmd["value"]
                target = cmd['target']
                action = "to" if value != "" else "on"
                text = f"*{command}* {value} {action}  *{target}*"
                if command == "open":
                    text = f"*{command}* {action} {target}"

                steps.append(f"{i}. {text}")

            steps = "\n".join(steps)

            summary = f"{d['scope'].capitalize()} [{d['name']}] {d['aggregation']} value violates threshold rule for {test_name}"

            description = f"""Value {d['actual']} violates threshold rule: {d['scope']} [{d['name']}] {d['aggregation']}
            {d['rule']} {d['expected']} for {test_name}"

                                      Steps:\n {steps}

                                      *Issue Hash:* {issue_hash}  
                        """

            fields_mapping = {
                "/fields/System.Title": summary,
                "/fields/Microsoft.VSTS.Common.Priority": PRIORITY_MAPPING['High'],
                "/fields/System.Description": description,
                "/fields/System.AreaPath": self.team,
                "/fields/System.IterationPath": self.team
            }

            body = []
            for key, value in fields_mapping.items():
                if value:
                    _piece = {"op": "add", "path": key, "value": value}
                    body.append(_piece)

            res = post(self.url, auth=self.auth, json=body,
                       headers={'content-type': 'application/json-patch+json'})

            logger.info(f"Azure DevOps issue {res.json()['id']} has been created")


def notify_azure_devops(test_name, threshold_results, args):
    caps = args['desired_capabilities']
    ado_organization = caps.get('ado_organization', '')
    ado_project = caps.get('ado_project', '')
    ado_token = caps.get('ado_token', '')
    ado_team = caps.get('ado_team', '')
    if ado_organization and ado_project and ado_token and ado_team:
        try:
            client = AdoClient(ado_organization, ado_project, ado_token, ado_team)
            client.create_issues(test_name, threshold_results["details"])
        except Exception as e:
            logger.error(f"Error during Azure DevOps ticket creation {e}")
