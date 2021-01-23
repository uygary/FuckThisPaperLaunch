import threading


# TODO: Properly use this via with as well.
class ThreadSafeCounter(object):
    def __init__(self):
        self._count = 0
        self._cost = 0.00
        self._lock = threading.Lock()

    def increment(self, count, cost):
        with self._lock:
            self._count += count
            self._cost += cost

    def get(self) -> (int, float):
        with self._lock:
            return (self._count, self._cost)
