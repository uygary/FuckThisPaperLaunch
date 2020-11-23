import time
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import presence_of_element_located,\
    element_to_be_clickable, \
    visibility_of_element_located
from selenium.common.exceptions import NoSuchElementException
from SellerException import SellerException
from Utility import Utility


class AmazonBuyer:
    CART_ENDPOINT = "/gp/cart/view.html/ref=nav_cart"
    EMPTY_CART_SELECTOR = "//div[@id='sc-active-cart']//h1[contains(text(), 'Your Amazon Cart is empty')]"

    def __init__(self,
                 chrome_driver_path,
                 affiliate_url,
                 item_endpoint,
                 whitelisted_sellers,
                 max_cost_per_item,
                 max_buy_count,
                 is_test_run,
                 timeout_in_seconds):
        self.chrome_driver_path = chrome_driver_path
        self.affiliate_url = affiliate_url
        self.item_endpoint = item_endpoint
        self.whitelisted_sellers = whitelisted_sellers
        self.max_cost_per_item = max_cost_per_item
        self.max_buy_count = max_buy_count
        self.is_test_run = is_test_run
        self.timeout_in_seconds = timeout_in_seconds

        self.item_url = f"{affiliate_url}{item_endpoint}"
        self.cart_url = f"{affiliate_url}{AmazonBuyer.CART_ENDPOINT}"

        self.is_authenticated = False
        self.current_buy_count = 0
        self.current_total_cost = 0.00

        try:
            self.browser = webdriver.Chrome(self.chrome_driver_path)
            self.browser.get(self.affiliate_url)
            self.wait = WebDriverWait(self.browser, self.timeout_in_seconds)
        except Exception as ex:
            Utility.log_error(f"Failed to open browser: {str(ex)}")
            raise

    def __del__(self):
        self.browser.quit()

    def try_authenticate(self, login_email: str, login_password: str) -> bool:
        try:
            self.browser.get(self.affiliate_url)
            self.wait.until(presence_of_element_located((By.LINK_TEXT, "Sign in")))
            # sign_in_link = self.browser.find_element(By.LINK_TEXT("Sign in"))
            sign_in_link = self.browser.find_element_by_link_text("Sign in")
            sign_in_link.click()

            self.wait.until(presence_of_element_located((By.ID, "ap_email")))
            email_input = self.browser.find_element_by_id("ap_email")
            email_input.send_keys(login_email)

            self.wait.until(presence_of_element_located((By.ID, "continue")))
            self.wait.until(element_to_be_clickable((By.ID, "continue")))
            continue_button = self.browser.find_element_by_id("continue")
            continue_button.click()

            self.wait.until(presence_of_element_located((By.ID, "ap_password")))
            password_input = self.browser.find_element_by_id("ap_password")
            password_input.send_keys(login_password)

            self.wait.until(presence_of_element_located((By.NAME, "rememberMe")))
            continue_button = self.browser.find_element_by_name("rememberMe")
            continue_button.click()

            self.wait.until(presence_of_element_located((By.ID, "signInSubmit")))
            self.wait.until(element_to_be_clickable((By.ID, "signInSubmit")))
            continue_button = self.browser.find_element_by_id("signInSubmit")
            continue_button.click()

            self.wait.until(presence_of_element_located((By.ID, "nav-item-signout")))
            Utility.log_verbose("Successfully logged in.")
            self.is_authenticated = True

            return True
        except Exception as ex:
            self.is_authenticated = False
            Utility.log_error(f"Failed to log in: {str(ex)}")

            return False

    def try_buy_item(self) -> bool:
        try:
            # Remove existing items from cart
            if not self.try_clear_cart():
                return False

            # Go to listing
            self.browser.get(self.item_url)

            # Check seller
            if not self.try_check_seller():
                return False

            # Attempt to use Buy Now
            if self.try_buy_now():
                return True

            # Remove existing items from cart
            if not self.try_clear_cart():
                return False

            # Go to listing
            self.browser.get(self.item_url)
            #self.browser.refresh()
            #self.browser.get(self.item_url)

            # Check seller
            if not self.try_check_seller():
                return False

            # Attempt to buy via cart
            return self.try_purchase_via_cart()
        except Exception as ex:
            Utility.log_verbose(f"Failed to buy item: {str(ex)}")
            return False

    def try_clear_cart(self):
        try:
            self.browser.get(self.cart_url)
            existing_cart_items_container = self.browser.find_element_by_id("activeCartViewForm")

            cart_empty = existing_cart_items_container.find_elements_by_xpath(AmazonBuyer.EMPTY_CART_SELECTOR)

            if len(cart_empty) == 1:
                return True

            existing_cart_items_to_delete = existing_cart_items_container.find_elements_by_xpath(
                "//form[@id='activeCartViewForm']//input[@value='Delete']")

            for existing_cart_item_to_delete in existing_cart_items_to_delete:
                existing_cart_item_to_delete.click()
                #time.sleep(3)

            self.wait.until(presence_of_element_located(
                (By.XPATH, AmazonBuyer.EMPTY_CART_SELECTOR)))
            self.wait.until(visibility_of_element_located(
                (By.XPATH, AmazonBuyer.EMPTY_CART_SELECTOR)))

            return True
        except Exception as ex:
            Utility.log_warning(f"Failed to clear cart: {str(ex)}")

            return False

    def try_check_seller(self):
        try:
            # Check if there are any whitelist rules defined
            if len(self.whitelisted_sellers) == 0:
                return True

            seller_info_container = self.browser.find_element_by_id("sellerProfileTriggerId")
            seller_info = seller_info_container.get_attribute("innerText")

            if all(seller_info not in seller for seller in self.whitelisted_sellers):
                raise SellerException("Seller is not whitelisted.")
        except SellerException as sex:
            Utility.log_verbose(f"Seller is not whitelisted: {str(sex)}")
            return False
        except NoSuchElementException as nex:
            Utility.log_verbose(f"Seller info not found. Assuming Amazon: {str(nex)}")
            return True
        except Exception as ex:
            Utility.log_error(f"Error occurred while trying to determine the seller: {str(ex)}")
            #raise
            return False    # We don't want to go ahead by an unwanted seller by mistake.

    def try_reject_additional_warranty(self):
        try:
            self.wait.until(presence_of_element_located((By.ID, "siNoCoverage-announce")))
            self.wait.until(visibility_of_element_located((By.ID, "siNoCoverage-announce")))
            self.wait.until(element_to_be_clickable((By.ID, "siNoCoverage-announce")))
            no_thanks = self.browser.find_element_by_id("siNoCoverage-announce")
            no_thanks.click()

            return True
        except Exception as ex:
            Utility.log_verbose(f'Assuming no "no thanks" is necessary: {str(ex)}')

            return False

    def try_buy_now(self):
        try:
            #self.wait.until(presence_of_element_located((By.ID, "buy-now-button")))
            #self.wait.until(visibility_of_element_located((By.ID, "buy-now-button")))
            #self.wait.until(element_to_be_clickable((By.ID, "buy-now-button")))
            buy_now_button = self.browser.find_element_by_id("buy-now-button")
            buy_now_button.click()
            #time.sleep(2)

            # Buy Now price check
            self.wait.until(presence_of_element_located((By.ID, "turbo-checkout-iframe")))
            self.wait.until(visibility_of_element_located((By.ID, "turbo-checkout-iframe")))
            buy_now_iframe = self.browser.find_element_by_id("turbo-checkout-iframe")
            self.browser.switch_to.frame(buy_now_iframe)
            self.wait.until(presence_of_element_located((By.ID, "turbo-checkout-panel-container")))
            self.wait.until(visibility_of_element_located((By.ID, "turbo-checkout-panel-container")))
            turbo_checkout_panel_container = self.browser.find_element_by_id("turbo-checkout-panel-container")
            buy_now_price_container = turbo_checkout_panel_container.find_element_by_xpath(
                "//div[@id='turbo-checkout-panel-container']//span[@class='a-color-price']")
            buy_now_price_text = buy_now_price_container.text

            buy_now_cost = Utility.parse_price_string(buy_now_price_text)
            if buy_now_cost > self.max_cost_per_item:
                Utility.log_information(f"Buy now price is too high: {buy_now_cost} instead of {self.max_cost_per_item}")
                self.browser.switch_to.parent_frame()

                return False

            self.wait.until(presence_of_element_located((By.ID, "turbo-checkout-pyo-button")))
            self.wait.until(visibility_of_element_located((By.ID, "turbo-checkout-pyo-button")))
            self.wait.until(element_to_be_clickable((By.ID, "turbo-checkout-pyo-button")))
            turbo_checkout_button = self.browser.find_element_by_id("turbo-checkout-pyo-button")

            if self.is_test_run:
                Utility.log_warning("Performing test run on Buy Now")
            else:
                turbo_checkout_button.click()

            # If we reached this far, it should mean success
            self.current_buy_count += 1
            self.current_total_cost += buy_now_cost
            Utility.log_warning(f"Purchased {self.current_buy_count} of {self.max_buy_count} via Buy Now at: {buy_now_cost}")
            self.browser.switch_to.parent_frame()

            return True
        except Exception as ex:
            Utility.log_verbose(f"Buy now did not work: {str(ex)}")
            self.browser.switch_to.parent_frame()

            return False

    def try_purchase_via_cart(self):
        try:
            add_to_cart_button = self.browser.find_element_by_id("add-to-cart-button")
            add_to_cart_button.click()
            time.sleep(2)

            self.try_reject_additional_warranty()

            self.browser.get(self.cart_url)

            checkout_button = self.browser.find_element_by_name("proceedToRetailCheckout")
            checkout_button.click()

            # Cart price check
            price_info = self.browser.find_element_by_css_selector("td.grand-total-price").text
            add_to_cart_cost = Utility.parse_price_string(price_info)
            if add_to_cart_cost > self.max_cost_per_item:
                Utility.log_information(f"Add to cart price is too high: {add_to_cart_cost} instead of {self.max_cost_per_item}")

                return False

            # Confirm order
            order_confirmation_button = self.browser.find_element_by_name("placeYourOrder1")

            if self.is_test_run:
                Utility.log_warning("Performing test run on Purchase via Cart")
            else:
                order_confirmation_button.click()

            self.current_buy_count += 1
            self.current_total_cost += add_to_cart_cost
            Utility.log_warning(f"Purchased {self.current_buy_count} of {self.max_buy_count} via Add to Cart at: {add_to_cart_cost}")

            return True

        except Exception as ex:
            Utility.log_verbose(f"Failed to buy item via cart. Current stock: {self.current_buy_count} of {self.max_buy_count} at: {self.current_total_cost}. Error was: {str(ex)}")

            return False
