class Success:
    def __init__(self, value=None):
        self.success = True
        self.failure = False
        self.value = value or self.success


class Failure:
    def __init__(self, error):
        self.success = False
        self.failure = True
        self.error = error


class Result:

    @staticmethod
    def from_success(value=None):
        return Success(value)

    @staticmethod
    def from_failure(err):
        return Failure(err)
