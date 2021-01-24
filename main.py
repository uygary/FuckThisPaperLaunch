# encoding: utf-8
import time
import os
import signal
import sys
import concurrent.futures
from os.path import join, dirname
from dotenv import load_dotenv
from Utility import Utility
from DisposableList import DisposableList
from ThreadSafeCounter import ThreadSafeCounter
from BuyerInterface import BuyerInterface
from AmazonBuyer import AmazonBuyer
from NeweggBuyer import NeweggBuyer
from WalmartBuyer import WalmartBuyer
from PurchaseProcessor import PurchaseProcessor
from chromedriver_py import binary_path as chrome_driver_path
from BrowserConnectionException import BrowserConnectionException
from pydoc import locate


load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

IS_TEST_RUN = Utility.get_config_value_bool("IS_TEST_RUN")
TIMEOUT_IN_SECONDS = Utility.get_config_value_int("TIMEOUT_IN_SECONDS")
MAX_RETRY_LIMIT = Utility.get_config_value_int("MAX_RETRY_LIMIT")

NUMBER_OF_ITEMS = Utility.get_config_value_int("NUMBER_OF_ITEMS")
ITEM_NAMES = list[str]()
ITEM_ENDPOINTS = list[str]()
MAX_BUY_COUNTS = list[int]()
MAX_COST_PER_ITEM_LIMITS = list[float]()
ITEM_COUNTERS = list[ThreadSafeCounter]()

ENABLED_BUYERS = Utility.get_config_value_str("ENABLED_BUYERS").split(",")

for i in range (NUMBER_OF_ITEMS):
    item_indice = i + 1    # Just to prevent counter-intuitive index in the configuration.
    ITEM_NAMES.append(Utility.get_config_value_str(f"ITEM_NAME_{item_indice}"))
    MAX_BUY_COUNTS.append(Utility.get_config_value_int(f"MAX_BUY_COUNT_{item_indice}"))
    MAX_COST_PER_ITEM_LIMITS.append(Utility.get_config_value_float(f"MAX_COST_PER_ITEM_{item_indice}"))
    ITEM_COUNTERS.append(ThreadSafeCounter())

if __name__ == "__main__":
    try:
        is_shutting_down = False
            
        # For semi-gracefully handling CTRL+C
        def break_handler(sig, frame):
            is_shutting_down = True
            for purchase_processor in purchase_processors:
                purchase_processor.is_shutting_down = True
            
        # Check out if we can trigger this without waiting for futures to complete.
        signal.signal(signal.SIGINT, break_handler)

        os.system('color')

        Utility.log_verbose(f"Using Chrome driver at: {chrome_driver_path}")

        # This still needs a lot of work. Is it worth investing in?
        BuyerInterface.register(AmazonBuyer)
        BuyerInterface.register(NeweggBuyer)
        BuyerInterface.register(WalmartBuyer)

        enabled_buyer_implementations = []
        for enabled_buyer in ENABLED_BUYERS:
            if enabled_buyer:
                enabled_buyer_implementations.append(locate(f"{enabled_buyer}.{enabled_buyer}"))

        # Launch browsers
        with DisposableList[PurchaseProcessor]() as purchase_processors:
            for i in range (NUMBER_OF_ITEMS):
                purchase_processor = PurchaseProcessor(chrome_driver_path,
                                                       i,
                                                       ITEM_NAMES[i],
                                                       MAX_BUY_COUNTS[i],
                                                       MAX_COST_PER_ITEM_LIMITS[i],
                                                       ITEM_COUNTERS[i],
                                                       MAX_RETRY_LIMIT,
                                                       TIMEOUT_IN_SECONDS,
                                                       IS_TEST_RUN,
                                                       *enabled_buyer_implementations)
                purchase_processors.append(purchase_processor)

            for purchase_processor in purchase_processors:
                if not is_shutting_down:
                    purchase_processor.initialize_buyers()

            def execute_purchase(purchase_processor):
                if not is_shutting_down and purchase_processor.item_counter.get()[0] < purchase_processor.max_buy_count:
                    purchase_processor.process_purchase()

            # Buy loops
            with concurrent.futures.ThreadPoolExecutor(len(purchase_processors)) as executor:
                executor.map(execute_purchase, purchase_processors)
                    
            for i in range(NUMBER_OF_ITEMS):
                current_purchase = ITEM_COUNTERS[i].get()

                Utility.log_warning(f"Purchased item #{i+1} ({ITEM_NAMES[i]}): {current_purchase[0]} item(s) at a total cost of: {current_purchase[1]}.")
    
    except Exception as ex:
        Utility.log_error(f"Unhandled exception occured: {str(ex)}")
        sys.exit(1)

    Utility.log_verbose("Shutting down...")
    sys.exit(0)
