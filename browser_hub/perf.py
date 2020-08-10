import base64
import copy
import os
import re
from multiprocessing import Pool
from subprocess import Popen, PIPE
from uuid import uuid4

from deepdiff import DeepDiff

from browser_hub import selenium
from browser_hub.audits import accessibility_audit, bestpractice_audit, performance_audit, privacy_audit
from browser_hub.constants import REPORT_PATH, FFMPEG_PATH


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
        if execution_result is None:
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

    report = reporter.save_report()


def sanitize(filename):
    return "".join(x for x in filename if x.isalnum())[0:25]


def trim_screenshot(kwargs):
    try:
        image_path = f'{os.path.join(kwargs["processing_path"], sanitize(kwargs["test_name"]), str(kwargs["ms"]))}_out.jpg'
        command = f'{FFMPEG_PATH} -ss {str(round(kwargs["ms"] / 1000, 3))} -i {kwargs["video_path"]} ' \
                  f'-vframes 1 {image_path}'
        Popen(command, stderr=PIPE, shell=True, universal_newlines=True).communicate()
        with open(image_path, "rb") as image_file:
            return {kwargs["ms"]: base64.b64encode(image_file.read()).decode("utf-8")}
    except FileNotFoundError:
        from traceback import format_exc
        print(format_exc())
        return {}


class HtmlReporter(object):
    def __init__(self, test_result, video_path, request_params, processing_path, screenshot_path):
        self.processing_path = processing_path
        self.title = request_params['info']['title']
        self.performance_timing = request_params['performancetiming']
        self.timing = request_params['timing']
        self.acc_score, self.acc_data = accessibility_audit(request_params['accessibility'])
        self.bp_score, self.bp_data = bestpractice_audit(request_params['bestPractices'])
        self.perf_score, self.perf_data = performance_audit(request_params['performance'])
        self.priv_score, self.priv_data = privacy_audit(request_params['privacy'])
        self.test_result = test_result

        base64_encoded_string = ""
        if screenshot_path:
            with open(screenshot_path, 'rb') as image_file:
                base64_encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

        self.html = self.generate_html(page_name=request_params['info']['title'],
                                       video_path=video_path,
                                       test_status=self.test_result,
                                       start_time=request_params['info'].get('testStart', 0),
                                       perf_score=self.perf_score,
                                       priv_score=self.priv_score,
                                       acc_score=self.acc_score,
                                       bp_score=self.bp_score,
                                       acc_findings=self.acc_data,
                                       perf_findings=self.perf_data,
                                       bp_findings=self.bp_data,
                                       priv_findings=self.priv_data,
                                       resource_timing=request_params['performanceResources'],
                                       marks=request_params['marks'],
                                       measures=request_params['measures'],
                                       navigation_timing=request_params['performancetiming'],
                                       info=request_params['info'],
                                       timing=request_params['timing'],
                                       base64_full_page_screen=base64_encoded_string)

    def concut_video(self, start, end, page_name, video_path):
        print(f"Concut video {video_path}")
        p = Pool(7)
        res = []
        try:
            page_name = page_name.replace(" ", "_")
            process_params = [{
                "video_path": video_path,
                "ms": part,
                "test_name": page_name,
                "processing_path": self.processing_path,
            } for part in range(start, end, (end - start) // 8)][1:]
            if not os.path.exists(os.path.join(self.processing_path, page_name)):
                os.mkdir(os.path.join(self.processing_path, sanitize(page_name)))
            res = p.map(trim_screenshot, process_params)
        except:
            from traceback import format_exc
            print(format_exc())
        finally:
            p.terminate()
        return res

    def generate_html(self, page_name, video_path, test_status, start_time, perf_score,
                      priv_score, acc_score, bp_score, acc_findings, perf_findings, bp_findings,
                      priv_findings, resource_timing, marks, measures, navigation_timing, info, timing,
                      base64_full_page_screen):
        from jinja2 import Environment, PackageLoader, select_autoescape
        env = Environment(
            loader=PackageLoader('browser_hub', 'templates'),
            autoescape=select_autoescape(['html', 'xml'])
        )

        last_response_end = max([resource['responseEnd'] for resource in resource_timing])
        end = int(max([navigation_timing['loadEventEnd'] - navigation_timing['navigationStart'], last_response_end]))
        screenshots = self.cut_video_to_screenshots(start_time, end, page_name, video_path)
        template = env.get_template('perfreport.html')

        res = template.render(page_name=page_name, test_status=test_status,
                              perf_score=perf_score, priv_score=priv_score, acc_score=acc_score, bp_score=bp_score,
                              screenshots=screenshots, full_page_screen=base64_full_page_screen,
                              acc_findings=acc_findings,
                              perf_findings=perf_findings,
                              bp_findings=bp_findings, priv_findings=priv_findings, resource_timing=resource_timing,
                              marks=marks, measures=measures, navigation_timing=navigation_timing,
                              info=info, timing=timing)

        return re.sub(r'[^\x00-\x7f]', r'', res)

    def cut_video_to_screenshots(self, start_time, end, page_name, video_path):
        if video_path is None:
            return []

        screenshots_dict = []
        for each in self.concut_video(start_time, end, page_name, video_path):
            if each:
                screenshots_dict.append(each)
        return [list(e.values())[0] for e in sorted(screenshots_dict, key=lambda d: list(d.keys()))]

    def save_report(self):
        report_uuid = uuid4()
        os.makedirs(REPORT_PATH, exist_ok=True)
        report_file_name = f'{REPORT_PATH}{self.title}_{report_uuid}.html'
        print(f"Generate html report {report_file_name}")
        with open(report_file_name, 'w') as f:
            f.write(self.html)
        # return HtmlReport(self.title, report_uuid)
