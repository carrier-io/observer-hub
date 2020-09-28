from observer_hub.models.exporters import JsonExporter
from observer_hub.models.thresholds import AggregatedThreshold, Threshold
from observer_hub.util import logger, filter_thresholds_for


def assert_test_thresholds(test_name, all_scope_thresholds, execution_results):
    threshold_results = {"total": len(all_scope_thresholds), "failed": 0, "details": []}

    if not all_scope_thresholds:
        return threshold_results

    logger.info(f"=====> Assert aggregated thresholds for {test_name}")
    checking_result = []
    for gate in all_scope_thresholds:
        threshold = AggregatedThreshold(gate, execution_results)
        if not threshold.is_passed():
            threshold_results['failed'] += 1
        checking_result.append(threshold.get_result())

    threshold_results["details"] = checking_result
    logger.info("=====>")

    return threshold_results


def assert_page_thresholds(execution_result, thresholds):
    page_identifier = execution_result.page_identifier
    scoped_thresholds = filter_thresholds_for(page_identifier, thresholds)

    threshold_results = {"total": len(scoped_thresholds), "failed": 0}
    if not thresholds:
        return threshold_results

    perf_results = JsonExporter(execution_result.results).export()['fields']

    logger.info(f"=====> Assert thresholds for {page_identifier}")
    for gate in scoped_thresholds:
        target_metric_name = gate["target"]
        threshold = Threshold(gate, perf_results[target_metric_name])
        if not threshold.is_passed():
            threshold_results['failed'] += 1
        threshold.get_result()

    logger.info("=====>")
    return threshold_results
