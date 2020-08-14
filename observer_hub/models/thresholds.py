from observer_hub.util import logger, is_values_match, get_aggregated_value, closest, flatten_list


class Threshold(object):

    def __init__(self, gate, actual):
        self.name = gate['target'].replace("_", " ").capitalize()
        self.gate = gate
        self.actual = actual
        self.expected = gate['metric']
        self.comparison = gate['comparison']
        self.scope = gate['scope']

    def is_passed(self):
        return is_values_match(self.actual, self.comparison, self.expected)

    def get_result(self):
        message = ""
        if not self.is_passed():
            message = f"Threshold: {self.scope} [{self.name}] value {self.actual} violates rule {self.comparison} {self.expected}"
            logger.info(f"{message}! [FAILED]")
        else:
            logger.info(
                f"Threshold: {self.scope} [{self.name}] value {self.actual} comply with rule {self.comparison} {self.expected}! [PASSED]")

        return {"name": f"{self.name}",
                "actual": self.actual, "expected": self.expected,
                "message": message}


class AggregatedThreshold(object):

    def __init__(self, gate, values):
        self.name = gate['target'].replace("_", " ").capitalize()
        self.metric_name = gate['target']
        self.expected_value = gate['metric']
        self.aggregation = gate['aggregation']
        self.comparison = gate['comparison']
        self.scope = gate['scope']
        self.values = values
        self.result = {}

    def get_actual_aggregated_value(self):
        if self.scope == 'every':
            for page, results in self.values.items():
                metrics = [d.to_json()[self.metric_name] for d in results]
                yield get_aggregated_value(self.aggregation, metrics)
        elif self.scope == 'all':
            result = []
            for page, results in self.values.items():
                metrics = [d.to_json()[self.metric_name] for d in results]
                result.append(metrics)

            yield get_aggregated_value(self.aggregation, flatten_list(result))
        else:
            result = {k: v for k, v in self.values.items() if k.startswith(self.scope)}
            for page, results in result.items():
                metrics = [d.to_json()[self.metric_name] for d in results]
                yield get_aggregated_value(self.aggregation, metrics)

    def is_passed(self):
        actual_value = None

        for actual, metrics in self.get_actual_aggregated_value():
            actual_value = actual

            if not is_values_match(actual, self.comparison, self.expected_value):
                message = f"Threshold: {self.scope} [{self.name}] {self.aggregation} value {actual} violates rule " \
                          f"{self.comparison} {self.expected_value}"
                logger.info(f"{message} [FAILED]")

                failed_result = self.__find_actual_result(metrics, actual)

                self.result = {
                    "name": f"{self.name}",
                    "status": "failed",
                    "rule": self.comparison,
                    "scope": self.scope,
                    "aggregation": self.aggregation,
                    "actual": actual,
                    "expected": self.expected_value,
                    "message": message,
                    "raw_result": failed_result
                }
                return False

        logger.info(
            f"Threshold: {self.scope} [{self.name}] {self.aggregation} value {actual_value} comply with rule {self.comparison} "
            f"{self.expected_value} [PASSED]")

        self.result = {
            "name": f"{self.name}",
            "status": "passed",
            "rule": self.comparison,
            "scope": self.scope,
            "aggregation": self.aggregation,
            "actual": actual_value,
            "expected": self.expected_value,
            "message": ''
        }

        return True

    def get_result(self):
        return self.result

    def __find_actual_result(self, metrics, actual):
        value = closest(metrics, actual)
        for _, data in self.values.items():
            for v in data:
                if v.to_json()[self.name.lower()] == value:
                    return v
