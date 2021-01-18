from Utility import Utility
from DisposableList import DisposableList
from ThreadSafeCounter import ThreadSafeCounter
from BuyerInterface import BuyerInterface
from BrowserConnectionException import BrowserConnectionException


class PurchaseProcessor():
    def __init__(self,
                 chrome_driver_path : str,
                 item_indice: int,
                 item_name: str,
                 max_buy_count: int,
                 max_cost_per_item: float,
                 item_counter: ThreadSafeCounter,
                 max_retry_limit: int,
                 timeout_in_seconds: int,
                 is_test_run: bool,
                 *buyer_implementations: BuyerInterface):
        #return super().__init__(*args, **kwargs)
        self.item_indice = item_indice
        self.item_name = item_name
        self.max_buy_count = max_buy_count
        self.item_counter = item_counter
        self.max_retry_limit = max_retry_limit
        self.timeout_in_seconds = timeout_in_seconds
        
        self.buyers = DisposableList[BuyerInterface]()
        for buyer_implementation in buyer_implementations:
            buyer = buyer_implementation(chrome_driver_path,
                                         item_indice,
                                         item_name,
                                         max_buy_count,
                                         max_cost_per_item,
                                         item_counter,
                                         max_retry_limit,
                                         timeout_in_seconds,
                                         is_test_run)
            self.buyers.append(buyer)

        self.is_shutting_down = False

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, ex_traceback):
        with self.buyers:
            pass

    def initialize_buyers(self) -> bool:
        for buyer in self.buyers:
            while not self.is_shutting_down and not buyer.is_authenticated:
                is_authenticated = buyer.try_authenticate()
                if is_authenticated:
                    break
                else:
                    time.sleep(self.timeout_in_seconds)
        return True

    def process_purchase(self) -> bool:
        is_item_bought = False
        for buyer in self.buyers:
            if not self.is_shutting_down and self.item_counter.get()[0] < self.max_buy_count:
                Utility.log_information(f"Current stock of item #{self.item_indice+1} ({self.item_name}): {self.item_counter.get()[0]} of {self.max_buy_count}.")
                try:
                    is_item_bought = is_item_bought or buyer.try_buy_item()
                    if is_item_bought:
                        Utility.log_warning(f"{buyer.BUYER_NAME} purchased {self.item_name}.")
                        Utility.beep()
                        current_count = self.item_counter.get()
                        Utility.log_warning(f"Current stock of item #{self.item_indice+1} ({self.item_name}): {current_count[0]} of {self.max_buy_count} at {current_count[1]}.")
                except BrowserConnectionException as cex:
                    Utility.log_error(f"{buyer.BUYER_NAME} faced fatal error trying to purchase {buyer.item_name}: {str(cex)}")
                    raise
        # Remember to add purchase detection.
        #time.sleep(TIMEOUT_IN_SECONDS)

        return is_item_bought