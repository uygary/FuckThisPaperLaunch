# encoding: utf-8
import time
import os
import sys
from distutils.util import strtobool
from os.path import join, dirname
from dotenv import load_dotenv
from Utility import Utility
from DisposableList import DisposableList
from ThreadSafeCounter import ThreadSafeCounter
from BuyerInterface import BuyerInterface
from AmazonBuyer import AmazonBuyer
from chromedriver_py import binary_path as chrome_driver_path


load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

AFFILIATE_URL = os.environ.get("AFFILIATE_URL")
WHITELISTED_SELLERS = os.environ.get("WHITELISTED_SELLERS").split(",")
BUY_NOW_ONLY = bool(strtobool(os.environ.get("BUY_NOW_ONLY")))
IS_TEST_RUN = bool(strtobool(os.environ.get("IS_TEST_RUN")))
TIMEOUT_IN_SECONDS = int(os.environ.get("TIMEOUT_IN_SECONDS"))

NUMBER_OF_ITEMS = int(os.environ.get("NUMBER_OF_ITEMS"))
LOGIN_EMAILS = list[str]()
LOGIN_PASSWORDS = list[str]()
ITEM_ENDPOINTS = list[str]()
MAX_BUY_COUNTS = list[int]()
MAX_COST_PER_ITEM_LIMITS = list[float]()
ITEM_COUNTERS = list[ThreadSafeCounter]()

for i in range (NUMBER_OF_ITEMS):
    item_indice = i + 1;    # Just to prevent counter-intuitive index in the configuration.
    LOGIN_EMAILS.append(os.environ.get(f"LOGIN_EMAIL_{item_indice}"))
    LOGIN_PASSWORDS.append(os.environ.get(f"LOGIN_PASSWORD_{item_indice}"))
    ITEM_ENDPOINTS.append(os.environ.get(f"ITEM_ENDPOINT_{item_indice}"))
    MAX_BUY_COUNTS.append(int(os.environ.get(f"MAX_BUY_COUNT_{item_indice}")))
    MAX_COST_PER_ITEM_LIMITS.append(float(os.environ.get(f"MAX_COST_PER_ITEM_{item_indice}")))
    ITEM_COUNTERS.append(ThreadSafeCounter())

if __name__ == "__main__":
    try:
        os.system('color')

        Utility.log_verbose(f"Using Chrome driver at: {chrome_driver_path}")

        # This still needs a lot of work. Is it worth investing in?
        BuyerInterface.register(AmazonBuyer)

        # Launch browsers
        with DisposableList[BuyerInterface]() as buyers:
            for i in range (NUMBER_OF_ITEMS):
                amazon_buyer = AmazonBuyer(chrome_driver_path,
                                   AFFILIATE_URL,
                                   ITEM_ENDPOINTS[i],
                                   WHITELISTED_SELLERS,
                                   MAX_COST_PER_ITEM_LIMITS[i],
                                   MAX_BUY_COUNTS[i],
                                   BUY_NOW_ONLY,
                                   IS_TEST_RUN,
                                   TIMEOUT_IN_SECONDS,
                                   ITEM_COUNTERS[i])
                
                buyers.append(amazon_buyer)

            # Authenticate
            for i in range (NUMBER_OF_ITEMS):
                buyer = buyers[i]
                while not buyer.is_authenticated:
                    is_authenticated = buyer.try_authenticate(LOGIN_EMAILS[i], LOGIN_PASSWORDS[i])
                    if is_authenticated:
                        break
                    else:
                        time.sleep(TIMEOUT_IN_SECONDS)

            # Buy loop
            for buyer in buyers:
                # This loop needs to go into a task/thread/coroutine/whatever.
                while buyer.item_counter.get()[0] < buyer.max_buy_count:
                    Utility.log_information(f"Current stock on buyer: {buyer.item_counter.get()[0]} of {buyer.max_buy_count}.")

                    # Inventory check
                    is_item_bought = buyer.try_buy_item()
                    if is_item_bought:
                        Utility.beep()
                        time.sleep(2 * TIMEOUT_IN_SECONDS)  # Need to add purchase success detection.
                    else:
                        time.sleep(TIMEOUT_IN_SECONDS)
                    
            for i in range(NUMBER_OF_ITEMS):
                current_purchase = ITEM_COUNTERS[i].get()

                Utility.log_warning(f"Purchased item #{i+1}: {current_purchase[0]} item(s) at a total cost of: {current_purchase[1]}.")
    except Exception as ex:
        Utility.log_error(f"Unhandled exception occured: {str(ex)}")
        sys.exit(1)

    Utility.log_verbose("Shutting down...")
    sys.exit(0)
