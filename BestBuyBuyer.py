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
class BestBuyBuyer(BuyerInterface, metaclass=abc.ABCMeta):
    BUYER_NAME = "BestBuyBuyer"
    SITE_AREA = "/site"
    LOGIN_ENDPOINT = "/identity/global/signin"
    CART_ENDPOINT = "/cart"

    SURVEY_WINDOW = "survey_window"
    SURVEY_NO_BUTTON = "survey_invite_no"
    MODAL_DIV = "//div[contains(@class, 'c-modal-grid')]"
    SIGNUP_BUTTON_SELECTOR = f"{MODAL_DIV}//input[@type='submit' and @data-track='Sign Up']"
    CLOSE_BUTTON_SELECTOR = f"{MODAL_DIV}//button[@type='button' and @aria-label='Close']"
    SIGNIN_BUTTON_SELECTOR = "//button[@type='submit' and text()='Sign In']"
    CONTINUE_BUTTON_SELECTOR = "//button[@type='submit' and text()='Continue']"
    SIGNING_SUCCESS_SELECTOR = "//button[@type='button' and @data-lid='hdr_signin']//span[starts-with(text(),'Hi, Uygar')]"

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
        super(BestBuyBuyer, self).__init__(chrome_driver_path,
                                          item_indice,
                                          item_name,
                                          max_buy_count,
                                          max_cost_per_item,
                                          item_counter,
                                          max_retry_limit,
                                          timeout_in_seconds,
                                          is_test_run)

        self.affiliate_url = Utility.get_config_value_str("BESTBUY_AFFILIATE_URL")
        self.item_endpoint = Utility.get_config_value_str(f"BESTBUY_ITEM_ENDPOINT_{self.item_indice+1}")
        self.login_url = f"{self.affiliate_url}{BestBuyBuyer.LOGIN_ENDPOINT}"
        self.item_url = f"{self.affiliate_url}{BestBuyBuyer.SITE_AREA}{self.item_endpoint}"
        self.cart_url = f"{self.affiliate_url}{BestBuyBuyer.CART_ENDPOINT}"
        self.stock_check_min_wait_in_seconds = Utility.get_config_value_int("BESTBUY_STOCK_CHECK_MIN_WAIT_IN_SECONDS")
        self.phone_confirmation_wait_in_seconds = Utility.get_config_value_int("BESTBUY_PHONE_CONFIRMATION_WAIT_IN_SECONDS")
        random.seed(time.time())

        self.is_authenticated = False
        try:
            self.browser = webdriver.Chrome(self.chrome_driver_path)
            self.browser.get(self.affiliate_url)
            self.wait = WebDriverWait(self.browser, self.timeout_in_seconds)
        except Exception as ex:
            Utility.log_error(f"{BestBuyBuyer.BUYER_NAME}::Failed to open browser: {str(ex)}")
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
            # Get rid of email/text signup modal if there one popped up.
            try:
                self.wait.until(presence_of_element_located((By.XPATH, BestBuyBuyer.MODAL_DIV)))
                self.wait.until(presence_of_element_located((By.XPATH, BestBuyBuyer.SIGNUP_BUTTON_SELECTOR)))
                self.wait.until(presence_of_element_located((By.XPATH, BestBuyBuyer.CLOSE_BUTTON_SELECTOR)))
            
                sign_in_link = self.browser.find_element_by_xpath(BestBuyBuyer.CLOSE_BUTTON_SELECTOR)
                sign_in_link.click()

                self.wait.until_not(presence_of_element_located((By.XPATH, BestBuyBuyer.SIGNUP_BUTTON_SELECTOR)))
            except Exception as rex:
                Utility.log_verbose(f"{BestBuyBuyer.BUYER_NAME}::No signup rejection necessary.")
            
            # Actually log in.
            self.browser.get(self.login_url)

            self.wait.until(presence_of_element_located((By.NAME, "fld-e")))
            self.wait.until(visibility_of_element_located((By.NAME, "fld-e")))

            email_input = self.browser.find_element_by_name("fld-e")
            login_email = Utility.get_config_value_str(f"BESTBUY_LOGIN_EMAIL_{self.item_indice+1}")
            email_input.send_keys(login_email)

            self.wait.until(presence_of_element_located((By.NAME, "fld-p1")))
            self.wait.until(visibility_of_element_located((By.NAME, "fld-p1")))
            
            password_input = self.browser.find_element_by_name("fld-p1")
            login_password = Utility.get_config_value_str(f"BESTBUY_LOGIN_PASSWORD_{self.item_indice+1}")
            password_input.send_keys(login_password)

            remember_me_checkbox = self.browser.find_element_by_id("cia-remember-me")
            remember_me_checkbox.click()
            
            self.wait.until(presence_of_element_located((By.XPATH, BestBuyBuyer.SIGNIN_BUTTON_SELECTOR)))
            self.wait.until(visibility_of_element_located((By.XPATH, BestBuyBuyer.SIGNIN_BUTTON_SELECTOR)))
            self.wait.until(element_to_be_clickable((By.XPATH, BestBuyBuyer.SIGNIN_BUTTON_SELECTOR)))
            sign_in_button = self.browser.find_element_by_xpath(BestBuyBuyer.SIGNIN_BUTTON_SELECTOR)
            sign_in_button.click()
            
            # 2FA via SMS. Doesn't happen frequently.
            # Might even be only once when a new account is created. I'm just not familiar with Best Buy.
            try:
                self.wait.until(presence_of_element_located((By.ID, "recoveryPhone")))
                self.wait.until(visibility_of_element_located((By.ID, "recoveryPhone")))
                self.wait.until(element_to_be_clickable((By.ID, "recoveryPhone")))
                recovery_phone_input = self.browser.find_element_by_id("recoveryPhone")
                recovery_phone = Utility.get_config_value_str(f"BESTBUY_RECOVERY_PHONE_{self.item_indice+1}")
                recovery_phone_input.send_keys(recovery_phone)
            
                self.wait.until(element_to_be_clickable((By.XPATH, BestBuyBuyer.CONTINUE_BUTTON_SELECTOR)))
                continue_button = self.browser.find_element_by_xpath(BestBuyBuyer.CONTINUE_BUTTON_SELECTOR)
                continue_button.click()

                # Wait for user to input and submit the verification code
                time.sleep(self.phone_confirmation_wait_in_seconds)
            except Exception as rex:
                Utility.log_verbose(f"{BestBuyBuyer.BUYER_NAME}::No recovery phone necessary.")
                
            # This should mean login was successful.
            self.wait.until(visibility_of_element_located((By.XPATH, BestBuyBuyer.SIGNING_SUCCESS_SELECTOR)))
            self.is_authenticated = True
            
            self.retry_counter = 0
            return True

        except (ProtocolError, MaxRetryError) as cex:
            Utility.log_error(f"{BestBuyBuyer.BUYER_NAME}::Cannot connect to Chrome: {str(cex)}")
            self.is_authenticated = False
            self.retry_counter += 1
            return False
        except Exception as ex:
            self.is_authenticated = False
            Utility.log_error(f"{BestBuyBuyer.BUYER_NAME}::Failed to log in: {str(ex)}")
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

            return self.try_purchase()

        except Exception as ex:
            Utility.log_verbose(f"{BestBuyBuyer.BUYER_NAME}::Failed to buy item: {str(ex)}")
            return False

    def try_clear_cart(self) -> bool:
        try:
            raise NotImplementedError("try_clear_cart is not implemented!")
        
            self.browser.get(self.cart_url)

            self.retry_counter = 0
            return True

        except (ProtocolError, MaxRetryError) as cex:
            Utility.log_error(f"{BestBuyBuyer.BUYER_NAME}::Cannot connect to Chrome: {str(cex)}")
            self.retry_counter += 1
            return False
        except Exception as ex:
            Utility.log_warning(f"{BestBuyBuyer.BUYER_NAME}::Failed to clear cart: {str(ex)}")
            return False

    def try_purchase(self) -> bool:
        try:
            raise NotImplementedError("try_purchase is not implemented!")
        
            self.browser.get(self.item_url)
            
            # Add to cart
            
            # Proceed to checkout
            
            # Check price
            if total_cost > self.max_cost_per_item:
                Utility.log_information(f"{BestBuyBuyer.BUYER_NAME}::Total price is too high: {total_cost} instead of {self.max_cost_per_item}")
                return False
            
            # Check if the item is already bought.
            with self.item_counter as locked_counter:
                if locked_counter.get_within_existing_lock()[0] >= max_buy_count:
                    return False
                
                # Check if this is a test run
                try:
                    if self.is_test_run:
                        Utility.log_warning(f"{BestBuyBuyer.BUYER_NAME}::Performing test run on Purchase.")
                        is_order_success = True
                    else:
                        # Purchase
                        is_order_success = True
                except Exception as sex:
                    Utility.log_verbose(f"{BestBuyBuyer.BUYER_NAME}::Couldn't perform summary action: {str(cex)}")
                    is_order_success = False
            
                if is_order_success:
                    locked_counter.increment_within_existing_lock(1, total_cost)
                    Utility.log_warning(f"{BestBuyBuyer.BUYER_NAME}::Purchased {locked_counter.get_within_existing_lock()[0]} of {self.max_buy_count} via Add to Cart at: {total_cost}")

            return is_order_success

        except Exception as ex:
            Utility.log_verbose(f"{BestBuyBuyer.BUYER_NAME}::Failed to buy item via cart. Current stock: {self.item_counter.get()[0]} of {self.max_buy_count} at: {self.item_counter.get()[1]}. Error was: {str(ex)}")

            return False

    def wait_pseudo_random(self):
        time_to_wait = self.stock_check_min_wait_in_seconds + random.randint(0, 15)
        time.sleep(time_to_wait)
