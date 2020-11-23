# encoding: utf-8
import time
import os
from distutils.util import strtobool
from os.path import join, dirname
from dotenv import load_dotenv
from Utility import Utility
from AmazonBuyer import AmazonBuyer


load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

CHROME_DRIVER_PATH = os.environ.get("CHROME_DRIVER_PATH")
LOGIN_EMAIL = os.environ.get("LOGIN_EMAIL")
LOGIN_PASSWORD = os.environ.get("LOGIN_PASSWORD")
AFFILIATE_URL = os.environ.get("AFFILIATE_URL")
ITEM_ENDPOINT = os.environ.get("ITEM_ENDPOINT")
WHITELISTED_SELLERS = os.environ.get("WHITELISTED_SELLERS").split(",")
MAX_COST_PER_ITEM = float(os.environ.get("MAX_COST_PER_ITEM"))
MAX_BUY_COUNT = int(os.environ.get("MAX_BUY_COUNT"))
BUY_NOW_ONLY = bool(strtobool(os.environ.get("BUY_NOW_ONLY")))
IS_TEST_RUN = bool(strtobool(os.environ.get("IS_TEST_RUN")))
TIMEOUT_IN_SECONDS = int(os.environ.get("TIMEOUT_IN_SECONDS"))


if __name__ == "__main__":
    try:
        os.system('color')
        
        # Launch browser
        with AmazonBuyer(CHROME_DRIVER_PATH,
                                   AFFILIATE_URL,
                                   ITEM_ENDPOINT,
                                   WHITELISTED_SELLERS,
                                   MAX_COST_PER_ITEM,
                                   MAX_BUY_COUNT,
                                   BUY_NOW_ONLY,
                                   IS_TEST_RUN,
                                   TIMEOUT_IN_SECONDS)\
        as amazon_buyer:

            # Authenticate
            while not amazon_buyer.is_authenticated:
                is_authenticated = amazon_buyer.try_authenticate(LOGIN_EMAIL, LOGIN_PASSWORD)
                if is_authenticated:
                    break
                else:
                    time.sleep(TIMEOUT_IN_SECONDS)

            # Buy loop
            while amazon_buyer.current_buy_count < MAX_BUY_COUNT:

                # Inventory check
                is_item_bought = amazon_buyer.try_buy_item()
                if is_item_bought:
                    time.sleep(2 * TIMEOUT_IN_SECONDS)  # Need to add purchase success detection.
                else:
                    time.sleep(TIMEOUT_IN_SECONDS)
                    
            Utility.log_warning(f"Purchased {amazon_buyer.current_buy_count} item(s) at a total cost of: {amazon_buyer.current_total_cost}.")
    except Exception as ex:
        Utility.log_error(f"Unhandled exception occured: {str(ex)}")
        exit()

    Utility.log_verbose("Shutting down...")
    exit()
