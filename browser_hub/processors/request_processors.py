import os
from urllib.parse import urlparse
from uuid import uuid4

from browser_hub.constants import SCREENSHOTS_PATH
from browser_hub.db import get_from_storage, save_to_storage
from browser_hub.models.execution_result import ExecutionResult
from browser_hub.processors.results_processor import compute_results_for_simple_page, compute_results_for_spa
from browser_hub.pert_agent import PerfAgent
from browser_hub.util import is_performance_entities_changed, is_dom_changed


def process_request(original_request, host, session_id, start_time, locators, commands):
    # host = request.host
    # port = request.port
    # session_id = request.path_components[3]
    perf_agent = PerfAgent(host, session_id)

    load_event_end = perf_agent.get_performance_timing()['loadEventEnd']
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
        page_identifier = get_page_identifier(current_url, results['info']['title'], original_request,
                                              locators[session_id])

    return ExecutionResult(page_identifier, results, screenshot_path, results_type)


def get_page_identifier(current_url, title, original_request, locators):
    parsed_url = urlparse(current_url)
    print("Get page identifier")
    print(original_request.path_components)

    if original_request.method == "DELETE":
        return f"{title}:{parsed_url.path}@close_browser()"

    command = original_request.path_components[6]
    element_id = original_request.path_components[5]
    locator = locators[element_id]

    return f"{title}:{parsed_url.path}@{command}({locator['using']}={locator['value']})"
