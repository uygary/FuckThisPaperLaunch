import abc
from abc import ABCMeta, abstractmethod
from ThreadSafeCounter import ThreadSafeCounter


class BuyerInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'try_authenticate')
                and callable(subclass.try_authenticate)
                and hasattr(subclass, 'try_buy_item')
                and callable(subclass.try_buy_item)
                and hasattr(subclass, '__del__')
                and callable(subclass.__del__)
                and hasattr(subclass, '__enter__')
                and callable(subclass.__enter__)
                and hasattr(subclass, '__exit__')
                and callable(subclass.__exit__)
                and hasattr(subclass, 'is_authenticated')
                and not callable(subclass.is_authenticated)
                and hasattr(subclass, 'item_counter')
                and not callable(subclass.item_counter)
                and hasattr(subclass, 'max_buy_count')
                and not callable(subclass.max_buy_count)
                and hasattr(subclass, 'item_indice')
                and not callable(subclass.item_indice)
                and hasattr(subclass, 'item_name')
                and not callable(subclass.item_name)
                and hasattr(subclass, 'BUYER_NAME')
                and not callable(subclass.BUYER_NAME))

    #@abc.abstractmethod
    @abstractmethod
    def __init__(self,
                 chrome_driver_path: str,
                 item_indice : int,
                 item_name: str,
                 max_buy_count: int,
                 max_cost_per_item: float,
                 item_counter: ThreadSafeCounter,
                 max_retry_limit: int,
                 timeout_in_seconds: int,
                 is_test_run: bool):
        self.chrome_driver_path = chrome_driver_path
        self.item_indice = item_indice
        self.item_name = item_name
        self.max_buy_count = max_buy_count
        self.max_cost_per_item = max_cost_per_item
        self.item_counter = item_counter
        self.max_retry_limit = max_retry_limit
        self.timeout_in_seconds = timeout_in_seconds
        self.is_test_run = is_test_run
        self.retry_counter = 0

    @abstractmethod
    def try_authenticate() -> bool:
        pass

    @abstractmethod
    def try_buy_item() -> bool:
        pass

    @abstractmethod
    def __enter__():
        pass

    @abstractmethod
    def __exit__():
        pass
