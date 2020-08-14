class ResultsCollector(object):

    def __init__(self):
        self.results = {}

    def add(self, page_identifier, data):

        if page_identifier in self.results.keys():
            self.results[page_identifier].append(data)
        else:
            self.results[page_identifier] = [data]
