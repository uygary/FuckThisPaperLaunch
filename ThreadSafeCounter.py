import threading


class ThreadSafeCounter(object):
    def __init__(self):
        self._value = 0
        self._lock = threading.Lock()

    def increment(self):
        with self._lock:
            self._value += 1

    def get(self) -> int:
        with self._lock:
            return self._value
