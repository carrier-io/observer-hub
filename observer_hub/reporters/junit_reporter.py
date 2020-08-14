from junit_xml import TestCase, TestSuite

from observer_hub.constants import RESULTS_REPORT_NAME
from observer_hub.util import logger


def generate_junit_report(test_name, total_thresholds):
    test_cases = []
    file_name = f"junit_report_{RESULTS_REPORT_NAME}.xml"
    logger.info(f"Generate report {file_name}")

    for item in total_thresholds["details"]:
        message = item['message']
        test_case = TestCase(item['name'], classname=f"{item['scope']}",
                             status="PASSED",
                             stdout=f"{item['scope']} {item['name'].lower()} {item['aggregation']} {item['actual']} "
                                    f"{item['rule']} {item['expected']}")
        if message:
            test_case.status = "FAILED"
            test_case.add_failure_info(message)
        test_cases.append(test_case)

    ts = TestSuite(test_name, test_cases)

    with open(f"/tmp/reports/{file_name}", 'w') as f:
        TestSuite.to_file(f, [ts], prettyprint=True)

    return file_name
