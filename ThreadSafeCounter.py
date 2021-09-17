import threading
from AccessViolationException import AccessViolationException


class ThreadSafeCounter(object):
    exception_message = "Cannot access unlocked resource!"

    def __init__(self):
        self._count = 0
        self._cost = 0.00
        self._lock = threading.Lock()

    def increment(self, count, cost):
        with self._lock:
            self._count += count
            self._cost += cost

    def increment_within_existing_lock(self, count, cost):
        if self._lock.locked():
            self._count += count
            self._cost += cost
        else:
            raise AccessViolationException(ThreadSafeCounter.exception_message)

    def get(self) -> (int, float):
        with self._lock:
            return (self._count, self._cost)

    def get_within_existing_lock(self):
        if self._lock.locked():
            return (self._count, self._cost)
        else:
            raise AccessViolationException(ThreadSafeCounter.exception_message)

    def __enter__():
        self._lock.acquire()
        return self

    def __exit__():
        self._lock.release()