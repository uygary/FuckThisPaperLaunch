import abc
import time
import os
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
class NeweggBuyer(BuyerInterface, metaclass=abc.ABCMeta):
    BUYER_NAME = "NeweggBuyer"
    LOGIN_ENDPOINT = "/NewMyAccount/AccountLogin.aspx"
    CART_ENDPOINT = "/shop/cart"
    LOGIN_BUTTON_SELECTOR = "//div[@class='nav-complex']/a[@class='nav-complex-inner']/div[@class='nav-complex-title' and text()='Sign in / Register']"
    CART_BUTTON_SELECTOR = "//div[@class='nav-complex']/a[@class='nav-complex-inner']/i[@class='fas fa-shopping-cart']"

    EMPTY_CART_SELECTOR = "//form//div[contains(@class, 'message')]//strong[text()='Oh...seems like the cart is empty...']"
    EMPTY_CART_SELECTOR_PARTIAL = "//div[@id='cart-root-container-content-skip']//span[@class='cart-list-pretitle' and text()='0 items in your cart']"

    CART_REMOVE_ALL_SELECTOR = "//div[@id='cart-top']//button[@data-target='#Popup_Remove_All']"
    CART_REMOVE_ALL_CONFIRMATION_SELECTOR = "//div[contains(@class, 'modal-dialog')]/div[@class='modal-content']/div[@class='modal-footer']/button[text()='Yes, Remove all of them.']"
    SELLER_SELECTOR = "//div[@class='product-buy-box']//div[@class='product-seller']/strong"

    CART_ITEM_DELETE_SELECTOR = "//div[@class='cart-content']//div[@class='cart-item-row']//div[contains(@class,'actions-container') and contains(@class,'action-button-container')]/button[@class='button button--link' and @data-automation-id='cart-item-remove']/span/span"
    CART_ITEM_COUNT_SELECTOR = "//div[@class='cart-content']/div[@class='text-left Grid']/div[@class='Grid-col u-size-1 u-size-9-12-m u-size-9-12-l ']/div[@class='cart-content-column']//div/h1[@id='cart-active-cart-heading']/span/span[2]/b"
    ADD_TO_CART_SELECTOR = "//div[@class='product-buy-box']//div[@id='ProductBuy']//button[text()='Add to cart ']"
    NO_THANKS_BUTTON_SELECTOR = "//div[@id='modal-intermediary']//div[@class='modal-content']//div[@class='modal-footer']/button[text()='No, thanks']"
    I_SAID_NO_THANKS_BUTTON_SELECTOR = "//div[@class='modal-content']/div[@class='modal-footer']//button[contains(text(), 'm not interested.')]"
    VIEW_CART_AND_CHECKOUT_SELECTOR = "//div[@id='modal-intermediary']//div[@class='modal-content']//div[@class='item-actions']/button[text()='View Cart & Checkout']"
    TOTAL_COST_SELECTOR = "//div[@class='summary-content']//li[@class='summary-content-total']/span"
    CHECKOUT_BUTTON_SELECTOR = "//div[@class='summary-content']//div[@class='summary-actions']/button[text()=' Secure Checkout ']"
    CONTINUE_TO_DELIVERY_BUTTON_SELECTOR = "//div[@class='checkout-step']/div[@class='checkout-step-action']/button[text()='Continue to delivery']"
    CONTINUE_TO_PAYMENT_BUTTON_SELECTOR = "//div[@class='checkout-step']/div[@class='checkout-step-action']/button[text()='Continue to payment']"
    CVV2_SELECTOR = "//div[contains(@class, 'card-default')]/ancestor::label[@class='card-info']/div[@class='retype-security-code']/input[@placeholder='CVV2']"
    REVIEW_ORDER_SELECTOR = "//div[@class='checkout-step-action']/button[text()='Review your order']"

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
        super(NeweggBuyer, self).__init__(chrome_driver_path,
                                          item_indice,
                                          item_name,
                                          max_buy_count,
                                          max_cost_per_item,
                                          item_counter,
                                          max_retry_limit,
                                          timeout_in_seconds,
                                          is_test_run)

        self.affiliate_url = Utility.get_config_value_str("NEWEGG_AFFILIATE_URL")
        self.secure_subdomain_url = Utility.get_config_value_str("NEWEGG_SECURE_SUBDOMAIN_URL")
        self.item_endpoint = Utility.get_config_value_str(f"NEWEGG_ITEM_ENDPOINT_{self.item_indice+1}")
        self.whitelisted_sellers = Utility.get_config_value_str("NEWEGG_WHITELISTED_SELLERS").split(",")
        self.login_url = f"{self.secure_subdomain_url}{NeweggBuyer.LOGIN_ENDPOINT}"
        self.item_url = f"{self.affiliate_url}{self.item_endpoint}"
        self.cart_url = f"{self.secure_subdomain_url}{NeweggBuyer.CART_ENDPOINT}"

        self.is_authenticated = False
        try:
            self.browser = webdriver.Chrome(self.chrome_driver_path)
            self.browser.get(self.affiliate_url)
            self.wait = WebDriverWait(self.browser, self.timeout_in_seconds)
        except Exception as ex:
            Utility.log_error(f"{NeweggBuyer.BUYER_NAME}::Failed to open browser: {str(ex)}")
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
            self.wait.until(presence_of_element_located((By.ID, "labeled-input-signEmail")))
            self.wait.until(visibility_of_element_located((By.ID, "labeled-input-signEmail")))

            email_input = self.browser.find_element_by_id("labeled-input-signEmail")
            login_email = Utility.get_config_value_str(f"NEWEGG_LOGIN_EMAIL_{self.item_indice+1}")
            email_input.send_keys(login_email)

            self.wait.until(presence_of_element_located((By.ID, "signInSubmit")))
            self.wait.until(visibility_of_element_located((By.ID, "signInSubmit")))
            
            sign_in_link = self.browser.find_element_by_id("signInSubmit")
            sign_in_link.click()

            self.wait.until(presence_of_element_located((By.ID, "labeled-input-password")))
            self.wait.until(visibility_of_element_located((By.ID, "labeled-input-password")))

            password_input = self.browser.find_element_by_id("labeled-input-password")
            login_password = Utility.get_config_value_str(f"NEWEGG_LOGIN_PASSWORD_{self.item_indice+1}")
            password_input.send_keys(login_password)

            self.wait.until(presence_of_element_located((By.ID, "signInSubmit")))
            self.wait.until(visibility_of_element_located((By.ID, "signInSubmit")))
            
            sign_in_link = self.browser.find_element_by_id("signInSubmit")
            sign_in_link.click()

            # This should mean login was successful.
            self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.CART_BUTTON_SELECTOR)))
            self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.CART_BUTTON_SELECTOR)))
            self.is_authenticated = True
            
            self.retry_counter = 0
            return True

        except (ProtocolError, MaxRetryError) as cex:
            Utility.log_error(f"{NeweggBuyer.BUYER_NAME}::Cannot connect to Chrome: {str(cex)}")
            self.is_authenticated = False
            self.retry_counter += 1
            return False
        except Exception as ex:
            self.is_authenticated = False
            Utility.log_error(f"{NeweggBuyer.BUYER_NAME}::Failed to log in: {str(ex)}")
            return False

    def try_buy_item(self) -> bool:
        if self.retry_counter == self.max_retry_limit:
            raise BrowserConnectionException("Maximum retry limit reached!")

        try:
            if not self.try_clear_cart():
                return False

            self.browser.get(self.item_url)

            if not self.try_check_seller():
                return False

            return self.try_purchase_via_cart()

        except Exception as ex:
            Utility.log_verbose(f"{NeweggBuyer.BUYER_NAME}::Failed to buy item: {str(ex)}")
            return False

    def try_clear_cart(self) -> bool:
        try:
            self.browser.get(self.cart_url)
            cart_empty = self.browser.find_elements_by_xpath(NeweggBuyer.EMPTY_CART_SELECTOR)

            if len(cart_empty) == 1:
                self.retry_counter = 0
                return True

            remove_all_button = self.browser.find_elements_by_xpath(NeweggBuyer.CART_REMOVE_ALL_SELECTOR)
            remove_all_button.click()
                
            self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.CART_REMOVE_ALL_CONFIRMATION_SELECTOR)))
            self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.CART_REMOVE_ALL_CONFIRMATION_SELECTOR)))

            remove_all_confirmation_button = self.browser.find_elements_by_xpath(NeweggBuyer.CART_REMOVE_ALL_CONFIRMATION_SELECTOR)
            remove_all_confirmation_button.click()
                
            self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.EMPTY_CART_SELECTOR)))
            self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.EMPTY_CART_SELECTOR)))

            self.retry_counter = 0
            return True

        except (ProtocolError, MaxRetryError) as cex:
            Utility.log_error(f"{NeweggBuyer.BUYER_NAME}::Cannot connect to Chrome: {str(cex)}")
            self.retry_counter += 1
            return False
        except Exception as ex:
            Utility.log_warning(f"{NeweggBuyer.BUYER_NAME}::Failed to clear cart: {str(ex)}")
            return False

    def try_check_seller(self) -> bool:
        try:
            if len(self.whitelisted_sellers) == 0:
                return True

            seller_info_container = self.browser.find_element_by_xpath(NeweggBuyer.SELLER_SELECTOR)
            seller_info = seller_info_container.get_attribute("innerText")

            if all(seller_info not in seller for seller in self.whitelisted_sellers):
                Utility.log_information(f"{NeweggBuyer.BUYER_NAME}::Seller is not whitelisted: {seller_info}")
                return False

            return True

        except Exception as ex:
            Utility.log_error(f"{NeweggBuyer.BUYER_NAME}::Error occurred while trying to determine the seller: {str(ex)}")
            return False

    def try_purchase_via_cart(self) -> bool:
        try:
            # Add to cart
            add_to_cart_button = self.browser.find_element_by_xpath(NeweggBuyer.ADD_TO_CART_SELECTOR)
            add_to_cart_button.click()

            # Thanks but you can shove that useless stuff that I've never asked for up your arse.
            try:
                self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.NO_THANKS_BUTTON_SELECTOR)))
                self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.NO_THANKS_BUTTON_SELECTOR)))
                
                no_thanks_button = self.browser.find_element_by_xpath(NeweggBuyer.NO_THANKS_BUTTON_SELECTOR)
                no_thanks_button.click()
            except Exception as nex:
                Utility.log_verbose(f'{NeweggBuyer.BUYER_NAME}::Assuming no "thanks but no thanks" is necessary: {str(nex)}')
            
            self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.VIEW_CART_AND_CHECKOUT_SELECTOR)))
            self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.VIEW_CART_AND_CHECKOUT_SELECTOR)))

            # Proceed to checkout
            proceed_to_checkout_button = self.browser.find_element_by_xpath(NeweggBuyer.VIEW_CART_AND_CHECKOUT_SELECTOR)
            proceed_to_checkout_button.click()

            # Thanks but you can shove that useless other stuff that I've never asked for up your arse.
            try:
                self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.I_SAID_NO_THANKS_BUTTON_SELECTOR)))
                self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.I_SAID_NO_THANKS_BUTTON_SELECTOR)))
                
                no_thanks_button = self.browser.find_element_by_xpath(NeweggBuyer.I_SAID_NO_THANKS_BUTTON_SELECTOR)
                no_thanks_button.click()
            except Exception as nex:
                Utility.log_verbose(f'{NeweggBuyer.BUYER_NAME}::Assuming still no "thanks but no thanks" is necessary: {str(nex)}')
            
            self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.TOTAL_COST_SELECTOR)))
            self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.TOTAL_COST_SELECTOR)))
            
            # Check price
            price_info = self.browser.find_element_by_xpath(NeweggBuyer.TOTAL_COST_SELECTOR).text
            total_cost = Utility.parse_price_string(price_info)
            if total_cost > self.max_cost_per_item:
                Utility.log_information(f"{NeweggBuyer.BUYER_NAME}::Total price is too high: {total_cost} instead of {self.max_cost_per_item}")
                return False

            checkout_button = self.browser.find_element_by_xpath(NeweggBuyer.CHECKOUT_BUTTON_SELECTOR)
            
            # Check if the item is already bought.
            if self.item_counter.get()[0] >= max_buy_count:
                return False
            
            # Purchase
            if self.is_test_run:
                Utility.log_warning(f"{NeweggBuyer.BUYER_NAME}::Performing test run on Purchase via Cart")
            else:
                checkout_button.click()

            self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.CONTINUE_TO_DELIVERY_BUTTON_SELECTOR)))
            self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.CONTINUE_TO_DELIVERY_BUTTON_SELECTOR)))
            continue_to_delivery_button = self.browser.find_element_by_xpath(NeweggBuyer.CONTINUE_TO_DELIVERY_BUTTON_SELECTOR)
            continue_to_delivery_button.click()

            self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.CONTINUE_TO_PAYMENT_BUTTON_SELECTOR)))
            self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.CONTINUE_TO_PAYMENT_BUTTON_SELECTOR)))
            continue_to_payment_button = self.browser.find_element_by_xpath(NeweggBuyer.CONTINUE_TO_PAYMENT_BUTTON_SELECTOR)
            
            # Check price
            price_info = self.browser.find_element_by_xpath(NeweggBuyer.TOTAL_COST_SELECTOR).text
            total_cost = Utility.parse_price_string(price_info)
            if total_cost > self.max_cost_per_item:
                Utility.log_information(f"{NeweggBuyer.BUYER_NAME}::Total price is too high: {total_cost} instead of {self.max_cost_per_item}")
                return False
            
            # Check if the item is already bought.
            if self.item_counter.get()[0] >= max_buy_count:
                return False

            continue_to_payment_button.click()
            
            # TODO: Check if we can use PayPal or BitPay easily.
            # Otherwise, having this in the config is bound to give me a heart attack and some nightmares.
            self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.CVV2_SELECTOR)))
            self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.CVV2_SELECTOR)))
            cvv2_input = self.browser.find_element_by_xpath(NeweggBuyer.CVV2_SELECTOR)

            cvv2 = Utility.get_config_value_str(f"WALMART_LOGIN_PASSWORD_{self.item_indice+1}")
            cvv2_input.send_keys(cvv2)

            self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.REVIEW_ORDER_SELECTOR)))
            self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.REVIEW_ORDER_SELECTOR)))
            review_order_button = self.browser.find_element_by_xpath(NeweggBuyer.REVIEW_ORDER_SELECTOR)
            review_order_button.click()

            ##################################################################
            # TODO: Handle the last pile of shite inside the payment iframe. #
            # Good for Newegg not to undertake PCI compliancy risks.         #
            # They seem to be a safe bet from the customer perpective.       #
            # But this redundancy is killing me from the bot perspective.    #
            ##################################################################

            self.item_counter.increment(1, add_to_cart_cost)
            Utility.log_warning(f"{NeweggBuyer.BUYER_NAME}::Purchased {self.item_counter.get()[0]} of {self.max_buy_count} via Add to Cart at: {add_to_cart_cost}")

            return True

        except Exception as ex:
            Utility.log_verbose(f"{NeweggBuyer.BUYER_NAME}::Failed to buy item via cart. Current stock: {self.item_counter.get()[0]} of {self.max_buy_count} at: {self.item_counter.get()[1]}. Error was: {str(ex)}")

            return False
