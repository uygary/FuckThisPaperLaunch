import abc
import time
import os
import random
from distutils.util import strtobool
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import presence_of_element_located,\
    element_to_be_clickable, \
    visibility_of_element_located, \
    text_to_be_present_in_element
from selenium.common.exceptions import NoSuchElementException
from urllib3.exceptions import ProtocolError
from urllib3.exceptions import MaxRetryError
from urllib3.exceptions import NewConnectionError
from BrowserConnectionException import BrowserConnectionException
from Utility import Utility
from ThreadSafeCounter import ThreadSafeCounter
from BuyerInterface import BuyerInterface


# TODO: Need to read through and sort these out.
@BuyerInterface.register
class WalmartBuyer(BuyerInterface, metaclass=abc.ABCMeta):
    BUYER_NAME = "WalmartBuyer"
    LOGIN_ENDPOINT = "/account/login"
    CART_ENDPOINT = "/cart"
    LOGIN_BUTTON_SELECTOR = "//button[@type='submit' and text()='Sign in']"
    EMPTY_CART_SELECTOR = "//div[@id='cart-root-container-content-skip']//span[@class='cart-list-pretitle' and text()='0 items in your cart']"
    CART_ITEM_DELETE_SELECTOR = "//div[@class='cart-content']//div[@class='cart-item-row']//div[contains(@class,'actions-container') and contains(@class,'action-button-container')]/button[@class='button button--link' and @data-automation-id='cart-item-remove']/span/span"
    CART_ITEM_COUNT_SELECTOR = "//div[@class='cart-content']/div[@class='text-left Grid']/div[@class='Grid-col u-size-1 u-size-9-12-m u-size-9-12-l ']/div[@class='cart-content-column']//div/h1[@id='cart-active-cart-heading']/span/span[2]/b"
    SELLER_SELECTOR = "//div[@id='product-overview']//div[@data-tl-id='ProductSellerInfo-ProductSellerInfo']/a[@class='seller-name']"
    ADD_TO_CART_SELECTOR = "//div[@id='add-on-atc-container']//div[contains(@class, 'prod-product-cta-add-to-cart')]/button[contains(@class, 'prod-ProductCTA--primary')]/span/span"
    PROCEEED_TO_CHECKOUT_SELECTOR = "//div[@class='PAC-pos']/div[contains(@class, 'pos-actions-container')]//div[contains(@class, 'cart-pos-proceed-to-checkout')]/div/button/span"
    CHECKOUT_BUTTON_SELECTOR = "//form[@name='order']//button[contains(@class, 'place-order-btn')]/span"
    TOTAL_COST_SELECTOR = "//div[contains(@class, 'checkout-responsive-container')]//div[contains(@class, 'persistent-order-summary')]/div[@class='order-summary']/div/div[@class='order-summary-grand-total order-summary-line']/span[contains(@class, 'order-summary-price text-right')]"

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
        super(WalmartBuyer, self).__init__(chrome_driver_path,
                                          item_indice,
                                          item_name,
                                          max_buy_count,
                                          max_cost_per_item,
                                          item_counter,
                                          max_retry_limit,
                                          timeout_in_seconds,
                                          is_test_run)

        self.affiliate_url = Utility.get_config_value_str("WALMART_AFFILIATE_URL")
        self.item_endpoint = Utility.get_config_value_str(f"WALMART_ITEM_ENDPOINT_{self.item_indice+1}")
        self.whitelisted_sellers = Utility.get_config_value_str("WALMART_WHITELISTED_SELLERS").split(",")
        self.login_url = f"{self.affiliate_url}{WalmartBuyer.LOGIN_ENDPOINT}"
        self.item_url = f"{self.affiliate_url}{self.item_endpoint}"
        self.cart_url = f"{self.affiliate_url}{WalmartBuyer.CART_ENDPOINT}"
        self.stock_check_min_wait_in_seconds = Utility.get_config_value_int("WALMART_STOCK_CHECK_MIN_WAIT_IN_SECONDS")
        random.seed(time.time())

        self.is_authenticated = False
        try:
            self.browser = webdriver.Chrome(self.chrome_driver_path)
            self.browser.get(self.affiliate_url)
            self.wait = WebDriverWait(self.browser, self.timeout_in_seconds)
        except Exception as ex:
            Utility.log_error(f"{WalmartBuyer.BUYER_NAME}::Failed to open browser: {str(ex)}")
            raise

    def __del__(self):
        self.browser.quit()

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, ex_traceback):
        self.browser.quit()

    def try_authenticate(self) -> bool:
        if self.retry_counter == self.max_retry_limit:
            raise BrowserConnectionException("Maximum retry limit reached!")

        try:
            self.browser.get(self.login_url)
            self.wait.until(presence_of_element_located((By.ID, "email")))
            self.wait.until(presence_of_element_located((By.ID, "password")))
            self.wait.until(presence_of_element_located((By.XPATH, WalmartBuyer.LOGIN_BUTTON_SELECTOR)))

            email_input = self.browser.find_element_by_id("email")
            login_email = Utility.get_config_value_str(f"WALMART_LOGIN_EMAIL_{self.item_indice+1}")
            email_input.send_keys(login_email)

            password_input = self.browser.find_element_by_id("password")
            login_password = Utility.get_config_value_str(f"WALMART_LOGIN_PASSWORD_{self.item_indice+1}")
            password_input.send_keys(login_password)
            
            sign_in_link = self.browser.find_element_by_xpath(WalmartBuyer.LOGIN_BUTTON_SELECTOR)
            sign_in_link.click()

            self.wait.until(presence_of_element_located((By.LINK_TEXT, "Sign Out")))
            Utility.log_verbose(f"{WalmartBuyer.BUYER_NAME}::Successfully logged in for {self.item_name}.")
            self.is_authenticated = True
            
            self.retry_counter = 0
            return True

        except (ProtocolError, MaxRetryError) as cex:
            Utility.log_error(f"{WalmartBuyer.BUYER_NAME}::Cannot connect to Chrome: {str(cex)}")
            self.is_authenticated = False
            self.retry_counter += 1
            return False
        except Exception as ex:
            self.is_authenticated = False
            Utility.log_error(f"{WalmartBuyer.BUYER_NAME}::Failed to log in: {str(ex)}")
            return False

    def try_buy_item(self) -> bool:
        if self.retry_counter == self.max_retry_limit:
            raise BrowserConnectionException("Maximum retry limit reached!")

        try:
            self.wait_pseudo_random()
            if not self.try_clear_cart():
                return False
            
            self.wait_pseudo_random()
            self.browser.get(self.item_url)

            if not self.try_check_seller():
                return False
            
            return self.try_purchase_via_cart()

        except Exception as ex:
            Utility.log_verbose(f"{WalmartBuyer.BUYER_NAME}::Failed to buy item: {str(ex)}")
            return False

    def try_clear_cart(self) -> bool:
        try:
            self.browser.get(self.cart_url)
            cart_empty = self.browser.find_elements_by_xpath(WalmartBuyer.EMPTY_CART_SELECTOR)

            if len(cart_empty) == 1:
                self.retry_counter = 0
                return True

            existing_cart_items_to_delete = self.browser.find_elements_by_xpath(WalmartBuyer.CART_ITEM_DELETE_SELECTOR)
            expected_item_count = int(self.browser.find_element_by_xpath(WalmartBuyer.CART_ITEM_COUNT_SELECTOR).text)

            for existing_cart_item_to_delete in existing_cart_items_to_delete:
                existing_cart_item_to_delete.click()
                expected_item_count -= 1
                #TODO: This still needs work.
                self.wait.until(text_to_be_present_in_element((By.XPATH,WalmartBuyer.CART_ITEM_COUNT_SELECTOR), str(expected_item_count)))
                
            self.wait.until(presence_of_element_located((By.XPATH, WalmartBuyer.EMPTY_CART_SELECTOR)))
            self.wait.until(visibility_of_element_located((By.XPATH, WalmartBuyer.EMPTY_CART_SELECTOR)))

            self.retry_counter = 0
            return True

        except (ProtocolError, MaxRetryError) as cex:
            Utility.log_error(f"{WalmartBuyer.BUYER_NAME}::Cannot connect to Chrome: {str(cex)}")
            self.retry_counter += 1
            return False
        except Exception as ex:
            Utility.log_warning(f"{WalmartBuyer.BUYER_NAME}::Failed to clear cart: {str(ex)}")
            return False

    def try_check_seller(self) -> bool:
        try:
            if len(self.whitelisted_sellers) == 0:
                return True

            seller_info_container = self.browser.find_element_by_xpath(WalmartBuyer.SELLER_SELECTOR)
            seller_info = seller_info_container.get_attribute("innerText")

            if all(seller_info not in seller for seller in self.whitelisted_sellers):
                Utility.log_information(f"{WalmartBuyer.BUYER_NAME}::Seller is not whitelisted: {seller_info}")
                return False

            return True

        except Exception as ex:
            Utility.log_error(f"{WalmartBuyer.BUYER_NAME}::Error occurred while trying to determine the seller: {str(ex)}")
            return False

    def try_purchase_via_cart(self) -> bool:
        try:
            # Add to cart
            add_to_cart_button = self.browser.find_element_by_xpath(WalmartBuyer.ADD_TO_CART_SELECTOR)
            add_to_cart_button.click()
            
            self.wait.until(presence_of_element_located((By.XPATH, WalmartBuyer.PROCEEED_TO_CHECKOUT_SELECTOR)))
            self.wait.until(visibility_of_element_located((By.XPATH, WalmartBuyer.PROCEEED_TO_CHECKOUT_SELECTOR)))

            # Proceed to checkout
            proceed_to_checkout_button = self.browser.find_element_by_xpath(WalmartBuyer.PROCEEED_TO_CHECKOUT_SELECTOR)
            proceed_to_checkout_button.click()
            
            self.wait.until(presence_of_element_located((By.XPATH, WalmartBuyer.TOTAL_COST_SELECTOR)))
            self.wait.until(visibility_of_element_located((By.XPATH, WalmartBuyer.TOTAL_COST_SELECTOR)))
            
            # Check price
            price_info = self.browser.find_element_by_xpath(WalmartBuyer.TOTAL_COST_SELECTOR).text
            total_cost = Utility.parse_price_string(price_info)
            if total_cost > self.max_cost_per_item:
                Utility.log_information(f"{WalmartBuyer.BUYER_NAME}::Total price is too high: {total_cost} instead of {self.max_cost_per_item}")
                return False
            
            checkout_button = self.browser.find_element_by_xpath(WalmartBuyer.CHECKOUT_BUTTON_SELECTOR)

            # Check if the item is already bought.
            with self.item_counter as locked_counter:
                if locked_counter.get_within_existing_lock()[0] >= max_buy_count:
                    return False

                # Purchase
                if self.is_test_run:
                    Utility.log_warning(f"{WalmartBuyer.BUYER_NAME}::Performing test run on Purchase via Cart")
                else:
                    checkout_button.click()
                
                # TODO: Add success detection.
                locked_counter.increment_within_existing_lock(1, total_cost)
            Utility.log_warning(f"{WalmartBuyer.BUYER_NAME}::Purchased {self.item_counter.get()[0]} of {self.max_buy_count} via Add to Cart at: {total_cost}")

            return True

        except Exception as ex:
            Utility.log_verbose(f"{WalmartBuyer.BUYER_NAME}::Failed to buy item via cart. Current stock: {self.item_counter.get()[0]} of {self.max_buy_count} at: {self.item_counter.get()[1]}. Error was: {str(ex)}")

            return False

    def wait_pseudo_random(self):
        time_to_wait = self.stock_check_min_wait_in_seconds + random.randint(0, 15)
        time.sleep(time_to_wait)
