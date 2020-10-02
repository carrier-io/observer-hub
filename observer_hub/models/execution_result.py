from observer_hub.models.exporters import JsonExporter


class ExecutionResult(object):

    def __init__(self, page_identifier=None, results=None, screenshot_path=None,
                 results_type="page", commands=None):
        self.page_identifier = page_identifier
        self.results = results
        self.screenshot_path = screenshot_path
        self.video_folder = None
        self.video_path = None
        self.results_type = results_type
        if not commands:
            commands = []
        self.commands = commands
        self.report = None

    def to_json(self):
        return JsonExporter(self.results).export()['fields']