class Flag:
    def __init__(self, val: bool = False):
        self._val = bool(val)

    def set_true(self):
        self._val = True

    def set_false(self):
        self._val = False

    def __bool__(self):
        return self._val
