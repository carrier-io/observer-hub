import hashlib

from jira import JIRA

from observer_hub.util import logger


class JiraClient(object):

    def __init__(self, url, user, password, project):
        self.url = url
        self.password = password
        self.user = user
        self.project = project.upper()
        self.client = self.__connect()

    def __connect(self):
        try:
            jira = JIRA(self.url, basic_auth=(self.user, self.password))
        except Exception as e:
            logger.error(f"Failed to connect to Jira {self.url} {e}")
            raise e

        projects = [project.key for project in jira.projects()]
        if self.project not in projects:
            raise Exception(f"No such project {self.project}")

        return jira

    def add_attachment(self, issue, report):
        if not report:
            return

        try:
            self.client.add_attachment(issue, attachment=report.path)
        except Exception as e:
            logger.error(e)

    def create_issues(self, scenario_name, data):
        for d in data:
            if d['status'] == 'passed':
                continue

            issue_hash = hashlib.sha256(
                f"{d['scope']} {d['name']} {d['aggregation']} {d['raw_result'].page_identifier}".encode(
                    'utf-8')).hexdigest()

            if len(self.get_issues(issue_hash)) > 0:
                logger.info(f"JIRA with hash {issue_hash} already exist")
                continue

            logger.info(f"=====> About to crate JIRA issues")

            steps = []
            for i, cmd in enumerate(d['raw_result'].commands, 1):
                command = cmd['command']
                value = cmd['value']
                action = "to" if value != "" else "on"
                target = cmd['target']
                text = f"*{command}* {value} {action}  *{target}*"
                if command == "open":
                    text = f"*{command}* {action} {target}"

                steps.append(f"{i}. {text}")

            steps = "\n".join(steps)

            summary = f"{d['scope'].capitalize()} [{d['name']}] {d['aggregation']} value violates threshold rule for {scenario_name}"

            description = f"""Value {d['actual']} violates threshold rule: {d['scope']} [{d['name']}] {d['aggregation']}
{d['rule']} {d['expected']} for {scenario_name}"
                          
                          Steps:\n {steps}
                          
                          *Issue Hash:* {issue_hash}  
            """

            field_list = {
                'project': {'key': self.project},
                'issuetype': 'Bug',
                'summary': summary,
                'description': description,
                'priority': {'name': "High"},
                'labels': ['observer', 'ui_performance', scenario_name]
            }

            issue = self.client.create_issue(field_list)
            self.add_attachment(issue, d['raw_result'].report)
            logger.info(f"JIRA {issue} has been created")

    def get_issues(self, issue_hash):
        issues = []
        i = 0
        chunk_size = 100
        while True:
            chunk = self.client.search_issues(
                f'project = {self.project} AND issuetype = Bug AND description ~ {issue_hash}', startAt=i,
                maxResults=chunk_size)
            i += chunk_size
            issues += chunk.iterable
            if i >= chunk.total:
                break
        return issues


def notify_jira(test_name, threshold_results, args):
    caps = args['desired_capabilities']
    jira_url = caps.get('jira_url', '')
    jira_project = caps.get('jira_project', '')
    jira_user = caps.get('jira_user', '')
    jira_password = caps.get('jira_password', '')

    if jira_url and jira_project:
        try:
            jira = JiraClient(jira_url, jira_user, jira_password, jira_project)
            jira.create_issues(test_name, threshold_results["details"])
        except Exception as e:
            logger.error(f"Error during jira ticket creation {e}")
