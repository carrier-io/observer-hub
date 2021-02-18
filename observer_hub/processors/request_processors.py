import os
from urllib.parse import urlparse
from uuid import uuid4

from observer_hub.constants import SCREENSHOTS_PATH
from observer_hub.db import get_from_storage, save_to_storage
from observer_hub.models.execution_result import ExecutionResult
from observer_hub.perf_agent import PerfAgent
from observer_hub.processors.results_processor import compute_results_for_simple_page, compute_results_for_spa
from observer_hub.util import is_performance_entities_changed, is_dom_changed, logger


def process_request(original_request, host, session_id, start_time, locators, commands):
    perf_agent = PerfAgent(host, session_id)

    performance_timing = perf_agent.get_performance_timing()
    if 'loadEventEnd' not in performance_timing.keys():
        return ExecutionResult()

    load_event_end = performance_timing['loadEventEnd']
    data = get_from_storage(session_id)

    results = None
    screenshot_path = None
    results_type = "page"

    if data is None or data['load_event_end'] != load_event_end:
        results = compute_results_for_simple_page(perf_agent)
        results['info']['title'] = perf_agent.page_title()
        dom = perf_agent.get_dom_size()

        save_to_storage(session_id, {
            "dom_size": dom,
            "results": results,
            "load_event_end": load_event_end,
            "perf_entities": []
        })

        results['info']['testStart'] = start_time
        results["info"]["url"] = perf_agent.get_current_url()
        results["info"]["headers"] = perf_agent.get_page_headers()

    else:
        perf_entities = data['perf_entities']
        old_dom = data['dom_size']
        previous_results = data['results']
        latest_pef_entries = perf_agent.get_performance_entities()

        is_entities_changed = is_performance_entities_changed(perf_entities, latest_pef_entries)
        new_dom = perf_agent.get_dom_size()
        if is_entities_changed and is_dom_changed(old_dom, new_dom):
            latest_results = perf_agent.get_performance_metrics()
            latest_results['info']['testStart'] = start_time
            results = compute_results_for_spa(previous_results, latest_results)

            save_to_storage(session_id, {
                "dom_size": new_dom,
                "results": latest_results,
                "load_event_end": load_event_end,
                "perf_entities": latest_pef_entries
            })

            results_type = "action"

    page_identifier = None
    if results:
        current_url = perf_agent.get_current_url()
        os.makedirs(SCREENSHOTS_PATH, exist_ok=True)
        screenshot_path = perf_agent.take_screenshot(f"{SCREENSHOTS_PATH}/{uuid4()}.png")
        page_identifier = get_page_identifier(current_url, results['info']['title'], original_request, locators,
                                              session_id)

    return ExecutionResult(page_identifier, results, screenshot_path, results_type, commands)


def get_page_identifier(current_url, title, original_request, locators, session_id):
    parsed_url = urlparse(current_url)
    logger.info(f"Get page identifier {original_request.path_components}")

    if original_request.method == "DELETE":
        locator = __find_actionable_locator(locators, len(locators))
        return f"{title}:{parsed_url.path}@{locator['action']}({locator['using']}={locator['value']})"

    if original_request.method == "POST" and original_request.path.endswith('/url'):
        locator = __find_actionable_locator(locators, len(locators))
        return f"{title}:{parsed_url.path}@{locator['action']}({locator['using']}={locator['value']})"

    current_element_id = original_request.path_components[5]

    if len(locators.keys()) == 2 and list(locators.keys())[0] == "open":
        url = locators['open']
        return f"{title}:{parsed_url.path}@open({url})"

    elements = list(locators.keys())
    current_element_index = elements.index(current_element_id)
    locator = __find_actionable_locator(locators, current_element_index)

    return f"{title}:{parsed_url.path}@{locator['action']}({locator['using']}={locator['value']})"


def __find_actionable_locator(locators, current_element_index):
    locator = {}
    for v in reversed(list(locators.values())[:current_element_index]):
        if isinstance(v, dict) and v.get('action') == 'click':
            locator = v
            break

    return locator
