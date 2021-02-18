import os
import shutil
from json import dumps
from uuid import uuid4
from observer_hub.video import get_video_length
from observer_hub.reporters.html_reporter import HtmlReport, HtmlReporter
from observer_hub.constants import REPORT_PATH


class MinioReporter(HtmlReporter):
    def __init__(self, test_result, video_path, request_params, processing_path, screenshot_path):
        super().__init__(test_result, video_path, request_params, processing_path, screenshot_path)

    def __report_specific(self, test_result, video_path, request_params, screenshot_path):
        screenshots = self.cut_video_to_screenshots(request_params['info'].get('testStart', 0),
                                                    get_video_length(video_path),
                                                    request_params['info']['title'],
                                                    video_path=video_path,
                                                    encode=False)
        self.package = dict(page_name=request_params['info'].get('testStart', 0), test_status=test_result,
                            screenshots=screenshots, full_page_screen=screenshot_path,
                            resource_timing=request_params['performanceResources'],
                            marks=self.__fix_details(request_params['marks']),
                            measures=self.__fix_details(request_params['measures']),
                            navigation_timing=request_params['performancetiming'],
                            info=request_params['info'], timing=request_params['timing'])

    def save_report(self):
        """
        creating zip with all required data
        :return: path
        """
        report_uuid = uuid4()
        os.makedirs(REPORT_PATH, exist_ok=True)
        minio_path = os.path.join(REPORT_PATH, f'{self.title}_{report_uuid}')
        minio_zip = f'{REPORT_PATH}/{self.title}_{report_uuid}.zip'
        os.makedirs(minio_path, exist_ok=True)
        with open(os.path.join(minio_path, 'package.json'), 'w') as f:
            f.write(dumps(self.package, indent=2))
        for screenshot in self.package["screenshots"]:
            f = screenshot[screenshot.keys()[0]]
            shutil.move(f["image_path"], os.path.join(minio_path, f['name']))
        shutil.make_archive(minio_zip, 'zip', minio_path)
        return HtmlReport(self.title, report_uuid, "zip")
