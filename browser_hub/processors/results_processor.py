import copy

from deepdiff import DeepDiff

from browser_hub.reporters.html_reporter import HtmlReporter


def compute_results_for_simple_page(perf_agent):
    metrics = perf_agent.get_performance_metrics()
    resources = copy.deepcopy(metrics['performanceResources'])

    sorted_items = sorted(resources, key=lambda k: k['startTime'])
    current_total = metrics['performancetiming']['loadEventEnd'] - metrics['performancetiming']['navigationStart']
    fixed_end = sorted_items[-1]['responseEnd']
    diff = fixed_end - current_total
    metrics['performancetiming']['loadEventEnd'] += round(diff)
    return metrics


# total_load_time = perf_timing['loadEventEnd'] - perf_timing['navigationStart']
# time_to_first_byte = perf_timing['responseStart'] - perf_timing['navigationStart']
# time_to_first_paint = timing['firstPaint']
# dom_content_loading = perf_timing['domContentLoadedEventStart'] - perf_timing['domLoading']
# dom_processing = perf_timing['domComplete'] - perf_timing['domLoading']
def compute_results_for_spa(old, new):
    result = copy.deepcopy(new)

    timing = {
        'connectEnd': 0,
        'connectStart': 0,
        'domComplete': 0,
        'domContentLoadedEventEnd': 0,
        'domContentLoadedEventStart': 0,
        'domInteractive': 0,
        'domLoading': 0,
        'domainLookupEnd': 0,
        'domainLookupStart': 0,
        'fetchStart': 0,
        'loadEventEnd': 0,
        'loadEventStart': 0,
        'navigationStart': 0,
        'redirectEnd': 0,
        'redirectStart': 0,
        'requestStart': 0,
        'responseEnd': 0,
        'responseStart': 0,
        'secureConnectionStart': 0,
        'unloadEventEnd': 0,
        'unloadEventStart': 0
    }

    diff = DeepDiff(old["performanceResources"], new["performanceResources"], ignore_order=True)

    removed = {}
    added = diff['iterable_item_added']
    if 'iterable_item_removed' in diff.keys():
        removed = diff['iterable_item_removed']

    items_added = []
    for key, item in added.items():
        if key not in removed.keys():
            items_added.append(item)

    sorted_items = sorted(items_added, key=lambda k: k['startTime'])

    fields = [
        'connectEnd',
        'connectStart',
        'domainLookupEnd',
        'domainLookupStart',
        'fetchStart',
        'requestStart',
        'responseEnd',
        'responseStart',
        'secureConnectionStart',
        'startTime'
    ]

    first_result = sorted_items[0]
    first_point = first_result['startTime']
    for item in sorted_items:
        for field in fields:
            curr_value = item[field]
            if curr_value == 0:
                continue
            item[field] = curr_value - first_point

    sorted_items = sorted(items_added, key=lambda k: k['responseEnd'])
    latest_response = round(sorted_items[-1]['responseEnd'])

    result["performanceResources"] = sorted_items
    timing['requestStart'] = round(first_result['requestStart'])
    timing['responseStart'] = round(first_result['responseStart'])
    timing['loadEventEnd'] = round(latest_response)

    content_loading_time = 0
    for item in sorted_items:
        if item['decodedBodySize'] > 0:
            content_loading_time += round(item["responseEnd"] - item["responseStart"])

    timing['domContentLoadedEventStart'] = 1
    timing['domContentLoadedEventEnd'] = timing['domContentLoadedEventStart']

    result['performancetiming'] = timing
    result['timing']['firstPaint'] = new['timing']['firstPaint'] - old['timing']['firstPaint']

    return result


def process_results_for_pages(scenario_results, thresholds):
    for execution_result in scenario_results:
        if execution_result.results is None:
            continue
        # threshold_results = assert_page_thresholds(execution_result, thresholds)

        report = generate_html_report(execution_result, [])
        # notify_on_command_end(report, execution_result, threshold_results)
        # execution_result.report = report


def generate_html_report(execution_result, threshold_results):
    print("=====> Reports generation")

    test_status = "passed"

    reporter = HtmlReporter(test_status, execution_result.video_path,
                            execution_result.results,
                            execution_result.video_folder,
                            execution_result.screenshot_path)

    return reporter.save_report()
