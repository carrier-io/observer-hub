class ExecutionResult(object):

    def __init__(self, results, screenshot_path):
        self.results = results
        self.screenshot_path = screenshot_path
        self.video_folder = None
        self.video_path = None
