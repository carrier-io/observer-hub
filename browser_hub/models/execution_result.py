class ExecutionResult(object):

    def __init__(self, page_identifier, results, screenshot_path=None, results_type="page"):
        self.page_identifier = page_identifier
        self.results = results
        self.screenshot_path = screenshot_path
        self.video_folder = None
        self.video_path = None
        self.results_type = results_type
        self.locators = []
