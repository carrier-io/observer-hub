from browser_hub import selenium
from browser_hub.db import get_from_storage, save_to_storage
from browser_hub.perf import compute_results_for_simple_page
from browser_hub.selenium import PerfAgent


def process_request(host, session_id):
    # host = request.host
    # port = request.port
    # session_id = request.path_components[3]
    perf_agent = PerfAgent(host, session_id)

    load_event_end = perf_agent.get_performance_timing()['loadEventEnd']
    data = get_from_storage(session_id)
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

        return results

    else:
        perf_entities = data['perf_entities']
        dom = data['dom_size']
        previous_results = data['results']
        print()
