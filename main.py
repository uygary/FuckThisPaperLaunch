# encoding: utf-8
import time
import os
import signal
import sys
import concurrent.futures
from distutils.util import strtobool
from os.path import join, dirname
from dotenv import load_dotenv
from Utility import Utility
from DisposableList import DisposableList
from ThreadSafeCounter import ThreadSafeCounter
from BuyerInterface import BuyerInterface
from AmazonBuyer import AmazonBuyer
from chromedriver_py import binary_path as chrome_driver_path
from BrowserConnectionException import BrowserConnectionException


load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

AFFILIATE_URL = os.environ.get("AFFILIATE_URL")
WHITELISTED_SELLERS = os.environ.get("WHITELISTED_SELLERS").split(",")
BUY_NOW_ONLY = bool(strtobool(os.environ.get("BUY_NOW_ONLY")))
IS_TEST_RUN = bool(strtobool(os.environ.get("IS_TEST_RUN")))
TIMEOUT_IN_SECONDS = int(os.environ.get("TIMEOUT_IN_SECONDS"))
MAX_RETRY_LIMIT = int(os.environ.get("MAX_RETRY_LIMIT"))

NUMBER_OF_ITEMS = int(os.environ.get("NUMBER_OF_ITEMS"))
ITEM_NAMES = list[str]()
LOGIN_EMAILS = list[str]()
LOGIN_PASSWORDS = list[str]()
ITEM_ENDPOINTS = list[str]()
MAX_BUY_COUNTS = list[int]()
MAX_COST_PER_ITEM_LIMITS = list[float]()
ITEM_COUNTERS = list[ThreadSafeCounter]()

for i in range (NUMBER_OF_ITEMS):
    item_indice = i + 1    # Just to prevent counter-intuitive index in the configuration.
    ITEM_NAMES.append(os.environ.get(f"ITEM_NAME_{item_indice}"))
    LOGIN_EMAILS.append(os.environ.get(f"LOGIN_EMAIL_{item_indice}"))
    LOGIN_PASSWORDS.append(os.environ.get(f"LOGIN_PASSWORD_{item_indice}"))
    ITEM_ENDPOINTS.append(os.environ.get(f"ITEM_ENDPOINT_{item_indice}"))
    MAX_BUY_COUNTS.append(int(os.environ.get(f"MAX_BUY_COUNT_{item_indice}")))
    MAX_COST_PER_ITEM_LIMITS.append(float(os.environ.get(f"MAX_COST_PER_ITEM_{item_indice}")))
    ITEM_COUNTERS.append(ThreadSafeCounter())

if __name__ == "__main__":
    try:
        is_shutting_down = False
        os.system('color')

        Utility.log_verbose(f"Using Chrome driver at: {chrome_driver_path}")

        # This still needs a lot of work. Is it worth investing in?
        BuyerInterface.register(AmazonBuyer)

        # Launch browsers
        with DisposableList[BuyerInterface]() as buyers:
            for i in range (NUMBER_OF_ITEMS):
                amazon_buyer = AmazonBuyer(chrome_driver_path,
                                   ITEM_NAMES[i],
                                   AFFILIATE_URL,
                                   ITEM_ENDPOINTS[i],
                                   WHITELISTED_SELLERS,
                                   MAX_COST_PER_ITEM_LIMITS[i],
                                   MAX_BUY_COUNTS[i],
                                   BUY_NOW_ONLY,
                                   IS_TEST_RUN,
                                   TIMEOUT_IN_SECONDS,
                                   ITEM_COUNTERS[i],
                                   MAX_RETRY_LIMIT)
                
                buyers.append(amazon_buyer)

            # Authenticate
            for i in range (len(buyers)):
                buyer = buyers[i]
                while not buyer.is_authenticated:
                    is_authenticated = buyer.try_authenticate(LOGIN_EMAILS[i], LOGIN_PASSWORDS[i])
                    if is_authenticated:
                        break
                    else:
                        time.sleep(TIMEOUT_IN_SECONDS)

            def execute_buyer(buyer):
                while not is_shutting_down and buyer.item_counter.get()[0] < buyer.max_buy_count:
                    Utility.log_information(f"Current stock on buyer: {buyer.item_counter.get()[0]} of {buyer.max_buy_count}.")

                    try:
                        # Inventory check
                        is_item_bought = buyer.try_buy_item()
                        if is_item_bought:
                            Utility.beep()
                            time.sleep(2 * TIMEOUT_IN_SECONDS)  # Need to add purchase success detection.
                        else:
                            time.sleep(TIMEOUT_IN_SECONDS)
                    except BrowserConnectionException as ex:
                        Utility.log_error(f"Buyer faced fatal error trying to purchase {buyer.item_name}: {str(ex)}")
                        raise
            
            # For semi-gracefully handling CTRL+C
            def break_handler(sig, frame):
                is_shutting_down = True
            
            # Why is this not working?
            signal.signal(signal.SIGINT, break_handler)

            # Buy loops
            with concurrent.futures.ThreadPoolExecutor(len(buyers)) as executor:
                executor.map(execute_buyer, buyers)
                    
            for i in range(NUMBER_OF_ITEMS):
                current_purchase = ITEM_COUNTERS[i].get()

                Utility.log_warning(f"Purchased item #{i+1} ({ITEM_NAMES[i]}): {current_purchase[0]} item(s) at a total cost of: {current_purchase[1]}.")
    
    except Exception as ex:
        Utility.log_error(f"Unhandled exception occured: {str(ex)}")
        sys.exit(1)

    Utility.log_verbose("Shutting down...")
    sys.exit(0)
