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
    
    CART_ITEM_DELETE_SELECTOR = "//div[@class='cart-content']//div[@class='cart-item-row']//div[contains(@class,'actions-container') and contains(@class,'action-button-container')]/button[@class='button button--link' and @data-automation-id='cart-item-remove']/span/span"
    CART_ITEM_DELETE_CONFIRMATION_SELECTOR = "//div[@class='modal-content']//button[text()='Yes, Remove all of them.']"
    CART_ITEM_COUNT_SELECTOR = "//div[@class='cart-content']/div[@class='text-left Grid']/div[@class='Grid-col u-size-1 u-size-9-12-m u-size-9-12-l ']/div[@class='cart-content-column']//div/h1[@id='cart-active-cart-heading']/span/span[2]/b"
    ADD_TO_CART_SELECTOR = "//div[@class='product-buy-box']//div[@id='ProductBuy']//button[text()='Add to cart ']"
    #NO_THANKS_BUTTON_SELECTOR = "//div[@id='modal-intermediary']//div[@class='modal-content']//div[@class='modal-footer']/button[text()='No, thanks']"
    NO_THANKS_BUTTON_SELECTOR = "//button[text()='No, thanks']"
    I_SAID_NO_THANKS_BUTTON_SELECTOR = "//div[@class='modal-content']/div[@class='modal-footer']//button[contains(text(), 'm not interested.')]"
    PISS_OFF_CHECKBOX_SELECTOR = "//div[@class='modal-content']/div[@class='modal-footer']//button[contains(text(), 'm not interested.')]/ancestor::div[@class='modal-footer']//label[contains(@class, 'form-checkbox')]"
    VIEW_CART_AND_CHECKOUT_SELECTOR = "//div[@id='modal-intermediary']//div[@class='modal-content']//div[@class='item-actions']/button[text()='View Cart & Checkout']"
    TOTAL_COST_SELECTOR = "//div[@class='summary-content']//li[@class='summary-content-total']/span"
    CHECKOUT_BUTTON_SELECTOR = "//div[@class='summary-content']//div[@class='summary-actions']/button[text()=' Secure Checkout ']"
    CONTINUE_TO_DELIVERY_BUTTON_SELECTOR = "//div[@class='checkout-step']/div[@class='checkout-step-action']/button[text()='Continue to delivery']"
    CONTINUE_TO_PAYMENT_BUTTON_SELECTOR = "//div[@class='checkout-step']/div[@class='checkout-step-action']/button[text()='Continue to payment']"
    #DEFAULT_CARD_CVV2_SELECTOR = "//div[contains(@class, 'card-default')]/ancestor::label[@class='card-info']/div[@class='retype-security-code']/input[@placeholder='CVV2']"
    #VERIFIED_CARD_CVV2_SELECTOR = "//div[@class='retype-security-code']/input[@placeholder='CVV2']"
    CVV2_SELECTOR = "//div[@class='retype-security-code']/input[@placeholder='CVV2']"
    REVIEW_ORDER_SELECTOR = "//div[@class='checkout-step-action']/button[text()='Review your order']"
    PLACE_ORDER_BUTTON_SELECTOR = "//button[@id='btnCreditCard']"
    ORDER_CONFIRMATION_MESSAGE_SELECTOR = "//div[@class='message-information']/span[@class='message-title']"
    ORDER_CONFIRMED_MESSAGE = "Thank you for your order!"

    LOGIN_VERIFICATION_SELECTOR = "//div[@class='signin-title' and text()='Security Code']/ancestor::div/form//div[@class='form-v-code']"
    #LOGIN_VERIFICATION_SELECTOR = "//div[@class='signin-title' and text()='Security Code']"
    SELLER_SELECTOR = "//div[@class='product-seller']/strong"
    POPUP_CLOSE_SELECTOR = "//a[@id='popup-close']"
    CENTER_POPUP_CLOSE_SELECTOR = "//a[contains(@class, 'centerPopup-close')]"
    SUMMARY_PLACE_ORDER_SELECTOR = "//div[@class='summary-actions']//button[@id='btnCreditCard']"

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
        self.login_confirmation_wait_in_seconds = Utility.get_config_value_int("NEWEGG_LOGIN_CONFIRMATION_WAIT_IN_SECONDS")

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

            # Let's get an input instead.
            # In fact, let's build a UI for this bot.
            try:
                self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.LOGIN_VERIFICATION_SELECTOR)))
                Utility.log_warning(f"{NeweggBuyer.BUYER_NAME}::Waiting for user to confirm login for {self.login_confirmation_wait_in_seconds} seconds.")
                login_confirmation_requested = True
                time.sleep(self.login_confirmation_wait_in_seconds)
            except Exception as vex:
                Utility.log_verbose(f"{NeweggBuyer.BUYER_NAME}::No login verification necessary.")
                login_confirmation_requested = False

            
            if not login_confirmation_requested:
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

            # Thanks but you can shove that useless other stuff that I've never asked for up your arse.
            try:
                self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.I_SAID_NO_THANKS_BUTTON_SELECTOR)))
                self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.I_SAID_NO_THANKS_BUTTON_SELECTOR)))
                self.wait.until(element_to_be_clickable((By.XPATH, NeweggBuyer.I_SAID_NO_THANKS_BUTTON_SELECTOR)))
                
                #do_not_show_again_checkbox = self.browser.find_element_by_xpath(NeweggBuyer.PISS_OFF_CHECKBOX_SELECTOR)
                #do_not_show_again_checkbox.click()

                no_thanks_button = self.browser.find_element_by_xpath(NeweggBuyer.I_SAID_NO_THANKS_BUTTON_SELECTOR)
                no_thanks_button.click()
            except Exception as nex:
                Utility.log_verbose(f'{NeweggBuyer.BUYER_NAME}::Assuming still no "thanks but no thanks" is necessary: {str(nex)}')

            remove_all_button = self.browser.find_element_by_xpath(NeweggBuyer.CART_REMOVE_ALL_SELECTOR)
            remove_all_button.click()
                
            self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.CART_REMOVE_ALL_CONFIRMATION_SELECTOR)))
            self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.CART_REMOVE_ALL_CONFIRMATION_SELECTOR)))
            self.wait.until(element_to_be_clickable((By.XPATH, NeweggBuyer.CART_REMOVE_ALL_CONFIRMATION_SELECTOR)))

            remove_all_confirmation_button = self.browser.find_element_by_xpath(NeweggBuyer.CART_REMOVE_ALL_CONFIRMATION_SELECTOR)
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
        
        except NoSuchElementException as nex:
            Utility.log_warning(f"{NeweggBuyer.BUYER_NAME}::Seller info not found. Assuming Newegg: {str(nex)}")
            return True
        except Exception as ex:
            Utility.log_error(f"{NeweggBuyer.BUYER_NAME}::Error occurred while trying to determine the seller: {str(ex)}")
            return False

    def try_purchase_via_cart(self) -> bool:
        try:
            #Shove all those popups up your arse please.
            try:
                self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.CENTER_POPUP_CLOSE_SELECTOR)))
                self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.CENTER_POPUP_CLOSE_SELECTOR)))
                self.wait.until(element_to_be_clickable((By.XPATH, NeweggBuyer.CENTER_POPUP_CLOSE_SELECTOR)))
                add_to_cart_button = self.browser.find_element_by_link_text("No, thanks. Don't ask again.")
                add_to_cart_button.click()
            except Exception as pex:
                Utility.log_verbose(f'{NeweggBuyer.BUYER_NAME}::Assuming no "close that shite center popup" is necessary: {str(pex)}')
            try:
                self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.POPUP_CLOSE_SELECTOR)))
                self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.POPUP_CLOSE_SELECTOR)))
                self.wait.until(element_to_be_clickable((By.XPATH, NeweggBuyer.POPUP_CLOSE_SELECTOR)))
                add_to_cart_button = self.browser.find_element_by_xpath(NeweggBuyer.POPUP_CLOSE_SELECTOR)
                add_to_cart_button.click()
            except Exception as pex:
                Utility.log_verbose(f'{NeweggBuyer.BUYER_NAME}::Assuming no "close that shite popup" is necessary: {str(pex)}')

            # Add to cart
            add_to_cart_button = self.browser.find_element_by_xpath(NeweggBuyer.ADD_TO_CART_SELECTOR)
            add_to_cart_button.click()

            # Thanks but you can shove that useless stuff that I've never asked for up your arse.
            try:
                self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.NO_THANKS_BUTTON_SELECTOR)))
                self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.NO_THANKS_BUTTON_SELECTOR)))
                self.wait.until(element_to_be_clickable((By.XPATH, NeweggBuyer.NO_THANKS_BUTTON_SELECTOR)))
                
                no_thanks_button = self.browser.find_element_by_xpath(NeweggBuyer.NO_THANKS_BUTTON_SELECTOR)
                no_thanks_button.click()
            except Exception as nex:
                Utility.log_verbose(f'{NeweggBuyer.BUYER_NAME}::Assuming no "thanks but no thanks" is necessary: {str(nex)}')
            
            self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.VIEW_CART_AND_CHECKOUT_SELECTOR)))
            self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.VIEW_CART_AND_CHECKOUT_SELECTOR)))
            self.wait.until(element_to_be_clickable((By.XPATH, NeweggBuyer.VIEW_CART_AND_CHECKOUT_SELECTOR)))

            # Proceed to checkout
            proceed_to_checkout_button = self.browser.find_element_by_xpath(NeweggBuyer.VIEW_CART_AND_CHECKOUT_SELECTOR)
            proceed_to_checkout_button.click()

            # Thanks but you can shove that useless other stuff that I've never asked for up your arse.
            try:
                self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.I_SAID_NO_THANKS_BUTTON_SELECTOR)))
                self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.I_SAID_NO_THANKS_BUTTON_SELECTOR)))
                self.wait.until(element_to_be_clickable((By.XPATH, NeweggBuyer.I_SAID_NO_THANKS_BUTTON_SELECTOR)))
                
                #do_not_show_again_checkbox = self.browser.find_element_by_xpath(NeweggBuyer.PISS_OFF_CHECKBOX_SELECTOR)
                #do_not_show_again_checkbox.click()
                
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
            if self.item_counter.get()[0] >= self.max_buy_count:
                return False
            
            # Purchase
            #if self.is_test_run:
            #    Utility.log_warning(f"{NeweggBuyer.BUYER_NAME}::Performing test run on Purchase.")
            #else:
            #    checkout_button.click()

            checkout_button.click()

            try:
                #self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.CONTINUE_TO_DELIVERY_BUTTON_SELECTOR)))
                #self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.CONTINUE_TO_DELIVERY_BUTTON_SELECTOR)))
                #self.wait.until(element_to_be_clickable((By.XPATH, NeweggBuyer.CONTINUE_TO_DELIVERY_BUTTON_SELECTOR)))
                continue_to_delivery_button = self.browser.find_element_by_xpath(NeweggBuyer.CONTINUE_TO_DELIVERY_BUTTON_SELECTOR)
                continue_to_delivery_button.click()
            except Exception as dex:
                Utility.log_verbose(f"{NeweggBuyer.BUYER_NAME}::Skipping delivery selection: {str(dex)}")

            should_continue_to_payment = False
            try:
                #self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.CONTINUE_TO_PAYMENT_BUTTON_SELECTOR)))
                #self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.CONTINUE_TO_PAYMENT_BUTTON_SELECTOR)))
                #self.wait.until(element_to_be_clickable((By.XPATH, NeweggBuyer.CONTINUE_TO_PAYMENT_BUTTON_SELECTOR)))
                continue_to_payment_button = self.browser.find_element_by_xpath(NeweggBuyer.CONTINUE_TO_PAYMENT_BUTTON_SELECTOR)
                should_continue_to_payment = True
            except Exception as pex:
                Utility.log_verbose(f"{NeweggBuyer.BUYER_NAME}::Skipping delivery selection: {str(pex)}")
            
            # Check price
            price_info = self.browser.find_element_by_xpath(NeweggBuyer.TOTAL_COST_SELECTOR).text
            total_cost = Utility.parse_price_string(price_info)
            if total_cost > self.max_cost_per_item:
                Utility.log_information(f"{NeweggBuyer.BUYER_NAME}::Total price is too high: {total_cost} instead of {self.max_cost_per_item}")
                return False
            
            # Check if the item is already bought.
            if self.item_counter.get()[0] >= self.max_buy_count:
                return False

            if should_continue_to_payment:
                continue_to_payment_button.click()
            
            try:
                # TODO: Check if we can use PayPal or BitPay easily.
                # Otherwise, having these in the config is bound to give me a heart attack and some nightmares.
                self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.CVV2_SELECTOR)))
                self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.CVV2_SELECTOR)))
                cvv2_input = self.browser.find_element_by_xpath(NeweggBuyer.CVV2_SELECTOR)

                cvv2 = Utility.get_config_value_str(f"NEWEGG_CVV2_{self.item_indice+1}")
                cvv2_input.send_keys(cvv2)
            except Exception as vex:
                Utility.log_warning(f"{NeweggBuyer.BUYER_NAME}::Failed to confirm CVV2. Assuming no confirmation necessary: {str(vex)}")

            try:
                self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.REVIEW_ORDER_SELECTOR)))
                self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.REVIEW_ORDER_SELECTOR)))
                self.wait.until(element_to_be_clickable((By.XPATH, NeweggBuyer.REVIEW_ORDER_SELECTOR)))
                review_order_button = self.browser.find_element_by_xpath(NeweggBuyer.REVIEW_ORDER_SELECTOR)
                review_order_button.click()
            except Exception as rex:
                Utility.log_warning(f"{NeweggBuyer.BUYER_NAME}::Failed to process order review. Assuming no review necessary: {str(rex)}")

            ##################################################################
            # TODO: Handle the last pile of shite inside the payment iframe. #
            # Good for Newegg not to undertake PCI compliancy risks.         #
            # They seem to be a safe bet from the customer perpective.       #
            # But this redundancy is killing me from the bot perspective.    #
            ##################################################################

            try:
                card_confirmation = self.browser.find_element_by_xpath("//div[contains(@id, 'zoid-ec-payment-')]/iframe")
                self.browser.switch_to.frame(card_confirmation)

                card_number_input = self.browser.find_element_by_xpath("//input[contains(@class, 'mask-cardnumber')]")
                card_number = Utility.get_config_value_str(f"NEWEGG_NEWEGG_CARD_NUMBER_{self.item_indice+1}")
                card_number_input.send_keys(card_number)

                save_button = self.browser.find_element_by_xpath("//div[@class='modal-footer']/button[text()='Save']")
                save_button.click()
            except Exception as cex:
                Utility.log_warning(f"{NeweggBuyer.BUYER_NAME}::Failed to process card confirmation iframe. Assuming no confirmation necessary: {str(cex)}")
                
            try:
                place_order_button = self.browser.find_element_by_xpath(NeweggBuyer.SUMMARY_PLACE_ORDER_SELECTOR)
                
                # Check if the item is already bought.
                if self.item_counter.get()[0] >= self.max_buy_count:
                    return False

                if self.is_test_run:
                    Utility.log_warning(f"{NeweggBuyer.BUYER_NAME}::Performing test run on Purchase.")
                    is_order_success = True
                else:
                    place_order_button.click()
            except Exception as sex:
                Utility.log_verbose(f"{NeweggBuyer.BUYER_NAME}::Couldn't perform summary action: {str(cex)}")

                self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.PLACE_ORDER_BUTTON_SELECTOR)))
                self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.PLACE_ORDER_BUTTON_SELECTOR)))
                self.wait.until(element_to_be_clickable((By.XPATH, NeweggBuyer.PLACE_ORDER_BUTTON_SELECTOR)))
            
                place_order_button = self.browser.find_element_by_xpath(NeweggBuyer.PLACE_ORDER_BUTTON_SELECTOR)
            
            if not is_order_success:
                # Check if the item is already bought.
                if self.item_counter.get()[0] >= self.max_buy_count:
                    return False

                # Purchase
                if self.is_test_run:
                    Utility.log_warning(f"{NeweggBuyer.BUYER_NAME}::Performing test run on Purchase.")
                    is_order_success = True
                else:
                    place_order_button.click()
                    self.wait.until(presence_of_element_located((By.XPATH, NeweggBuyer.ORDER_CONFIRMATION_MESSAGE_SELECTOR)))
                    self.wait.until(visibility_of_element_located((By.XPATH, NeweggBuyer.ORDER_CONFIRMATION_MESSAGE_SELECTOR)))
                    confirmation_message = self.browser.find_element_by_xpath(NeweggBuyer.PLACE_ORDER_BUTTON_SELECTOR).text
                    is_order_success = confirmation_message == NeweggBuyer.ORDER_CONFIRMED_MESSAGE

            if is_order_success:
                self.item_counter.increment(1, total_cost)
                Utility.log_warning(f"{NeweggBuyer.BUYER_NAME}::Purchased {self.item_counter.get()[0]} of {self.max_buy_count} via Add to Cart at: {total_cost}")

            return is_order_success

        except Exception as ex:
            Utility.log_verbose(f"{NeweggBuyer.BUYER_NAME}::Failed to buy item via cart. Current stock: {self.item_counter.get()[0]} of {self.max_buy_count} at: {self.item_counter.get()[1]}. Error was: {str(ex)}")

            return False
