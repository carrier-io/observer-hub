class ExecutionResult(object):

    def __init__(self, results, screenshot_path=None, results_type="page"):
        self.results = results
        self.screenshot_path = screenshot_path
        self.video_folder = None
        self.video_path = None
        self.results_type = results_type
        self.locators = []
