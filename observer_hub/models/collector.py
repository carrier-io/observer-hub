class Collector(object):

    def __init__(self):
        self.data = {}

    def add(self, key, data):

        if key in self.data.keys():
            self.data[key].append(data)
        else:
            self.data[key] = [data]

    def pop(self, k, default=None):
        self.data.pop(k, default)

    def __getitem__(self, key):
        return self.data[key]

    def keys(self):
        return self.data.keys()


class ExecutionResultsCollector(Collector):

    def __init__(self):
        super().__init__()


class ResultsCollector(Collector):

    def __init__(self):
        super().__init__()


class CommandsCollector(Collector):

    def __init__(self):
        super().__init__()


class LocatorsCollector(Collector):
    def __init__(self):
        super().__init__()

    def save(self, session_id, element_id, locator):
        if session_id in self.data.keys():
            self.data[session_id][element_id] = locator
        else:
            self.data[session_id] = {element_id: locator}
