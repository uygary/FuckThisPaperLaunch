# encoding: utf-8
import sys
import time
import os
from os.path import join, dirname
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import presence_of_element_located,\
    element_to_be_clickable, \
    visibility_of_element_located
from selenium.webdriver.support.wait import WebDriverWait

load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

CHROME_DRIVER_PATH = os.environ.get("CHROME_DRIVER_PATH")
LOGIN_EMAIL = os.environ.get("LOGIN_EMAIL")
LOGIN_PASSWORD = os.environ.get("LOGIN_PASSWORD")
AFFILIATE_URL = os.environ.get("AFFILIATE_URL")
ITEM_URL = f"{AFFILIATE_URL}{os.environ.get('ITEM_ENDPOINT')}"
CART_URL = f"{AFFILIATE_URL}/gp/cart/view.html/ref=nav_cart"
WHITELISTED_SELLERS = os.environ.get("WHITELISTED_SELLERS").split(",")
MAX_COST = float(os.environ.get("MAX_COST"))
MAX_BUY_COUNT = int(os.environ.get("MAX_BUY_COUNT"))

buy_count = 0
total_cost = 0.00


class SellerError(Exception):
    pass


def log(log_message):
    print(f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}::{log_message}")


def parse_price_string(price_string):
    cleaned_price_string = price_string\
        .replace(",", "")\
        .replace("$", "")\
        .replace("£", "")\
        .replace("€", "")
    parsed_price = float(cleaned_price_string)
    return parsed_price


if __name__ == "__main__":

    # Launch browser
    try:
        browser = webdriver.Chrome(CHROME_DRIVER_PATH)
        browser.get(AFFILIATE_URL)
        wait = WebDriverWait(browser, 5)
    except Exception as e:
        log(f"Failed to open browser: {str(e)}")
        exit()

    # Authenticate
    while buy_count < MAX_BUY_COUNT:
        try:
            wait.until(presence_of_element_located((By.LINK_TEXT, "Sign in")))
            #sign_in_link = browser.find_element(By.LINK_TEXT("Sign in"))
            sign_in_link = browser.find_element_by_link_text("Sign in")
            sign_in_link.click()

            wait.until(presence_of_element_located((By.ID, "ap_email")))
            email_input = browser.find_element_by_id("ap_email")
            email_input.send_keys(LOGIN_EMAIL)

            wait.until(presence_of_element_located((By.ID, "continue")))
            wait.until(element_to_be_clickable((By.ID, "continue")))
            continue_button = browser.find_element_by_id("continue")
            continue_button.click()

            wait.until(presence_of_element_located((By.ID, "ap_password")))
            password_input = browser.find_element_by_id("ap_password")
            password_input.send_keys(LOGIN_PASSWORD)

            wait.until(presence_of_element_located((By.NAME, "rememberMe")))
            continue_button = browser.find_element_by_name("rememberMe")
            continue_button.click()

            wait.until(presence_of_element_located((By.ID, "signInSubmit")))
            wait.until(element_to_be_clickable((By.ID, "signInSubmit")))
            continue_button = browser.find_element_by_id("signInSubmit")
            continue_button.click()

            wait.until(presence_of_element_located((By.ID, "nav-item-signout")))
            log("Successfully logged in.")
            break
        except Exception as e:
            log(f"Failed to log in: {str(e)}")
            time.sleep(10)
            browser.get(AFFILIATE_URL)

    # Buy loop
    while buy_count < MAX_BUY_COUNT:
        # Remove existing items from cart
        browser.get(CART_URL)
        existing_cart_items_container = browser.find_element_by_id("activeCartViewForm")
        existing_cart_items_to_delete = existing_cart_items_container.find_elements_by_xpath("//form[@id='activeCartViewForm']//input[@value='Delete']")
        for existing_cart_item_to_delete in existing_cart_items_to_delete:
            existing_cart_item_to_delete.click()
            time.sleep(5)

        # Inventory check
        browser.get(ITEM_URL)
        while buy_count < MAX_BUY_COUNT:
            try:
                # Seller profile check
                try:
                    seller_info_container = browser.find_element_by_id("sellerProfileTriggerId")
                    seller_info = seller_info_container.get_attribute("innerText")

                    if all(seller_info not in seller for seller in WHITELISTED_SELLERS):
                        raise SellerError("Seller is not whitelisted.")
                except NoSuchElementException as ne:
                    log(f"Seller info not found. Assuming Amazon: {str(ne)}")
                    pass
                except SellerError as se:
                    log(f"Seller is not whitelisted: {str(se)}")
                    raise
                except Exception as e:
                    log(f"Error occurred while trying to determine the seller: {str(e)}")
                    raise

                # Attempt to use Buy Now
                try:
                    buy_now_button = browser.find_element_by_id("buy-now-button")
                    buy_now_button.click()
                    #time.sleep(2)

                    # Buy Now price check
                    wait.until(presence_of_element_located((By.ID, "turbo-checkout-iframe")))
                    wait.until(visibility_of_element_located((By.ID, "turbo-checkout-iframe")))
                    buy_now_iframe = browser.find_element_by_id("turbo-checkout-iframe")
                    browser.switch_to.frame(buy_now_iframe)
                    wait.until(presence_of_element_located((By.ID, "turbo-checkout-panel-container")))
                    wait.until(visibility_of_element_located((By.ID, "turbo-checkout-panel-container")))
                    turbo_checkout_panel_container = browser.find_element_by_id("turbo-checkout-panel-container")
                    buy_now_price_container = turbo_checkout_panel_container.find_element_by_xpath(
                        "//div[@id='turbo-checkout-panel-container']//span[@class='a-color-price']")
                    buy_now_price_text = buy_now_price_container.text

                    buy_now_cost = parse_price_string(buy_now_price_text)
                    if buy_now_cost > MAX_COST:
                        log(f"Buy now price is too high: {buy_now_cost} instead of {MAX_COST}")
                        browser.switch_to.parent_frame()
                        browser.refresh()
                        continue

                    wait.until(presence_of_element_located((By.ID, "turbo-checkout-pyo-button")))
                    wait.until(visibility_of_element_located((By.ID, "turbo-checkout-pyo-button")))
                    wait.until(element_to_be_clickable((By.ID, "turbo-checkout-pyo-button")))
                    turbo_checkout_button = browser.find_element_by_id("turbo-checkout-pyo-button")
                    turbo_checkout_button.click()
                    time.sleep(15)

                    # If we reached this far, it should mean success
                    buy_count += 1
                    total_cost += buy_now_cost
                    log(f"Purchased {buy_count} of {MAX_BUY_COUNT} via Buy Now at: ${buy_now_cost}")
                    browser.switch_to.parent_frame()
                    browser.get(ITEM_URL)
                    continue
                except Exception as e:
                    log(f"Buy now did not work: {str(e)}")
                    browser.switch_to.parent_frame()
                    pass

                # Attempt to use Add to Cart
                add_to_cart_button = browser.find_element_by_id("add-to-cart-button")
                add_to_cart_button.click()
                time.sleep(2)

                # Reject any additional warranty and similar nonsense
                try:
                    wait.until(presence_of_element_located((By.ID, "siNoCoverage-announce")))
                    wait.until(visibility_of_element_located((By.ID, "siNoCoverage-announce")))
                    wait.until(element_to_be_clickable((By.ID, "siNoCoverage-announce")))
                    no_thanks = browser.find_element_by_id("siNoCoverage-announce")
                    no_thanks.click()
                except Exception as e:
                    log(f'Assuming no "no thanks" is necessary: {str(e)}')
                    pass
                break
            except Exception as e:
                log(f"Failed to add item to cart. Current stock: {buy_count} of {MAX_BUY_COUNT} at: ${total_cost}. Error was: {str(e)}")
                time.sleep(5)
                browser.refresh()

        # Continue to purchase
        browser.get(CART_URL)

        checkout_button = browser.find_element_by_name("proceedToRetailCheckout")
        checkout_button.click()

        # Check price
        price_info = browser.find_element_by_css_selector("td.grand-total-price").text
        add_to_cart_cost = parse_price_string(price_info)
        if add_to_cart_cost > MAX_COST:
            log(f"Add to cart price is too high: {add_to_cart_cost} instead of {MAX_COST}")
            continue

        # Confirm order
        order_confirmation_button = browser.find_element_by_name("placeYourOrder1")
        order_confirmation_button.click()
        time.sleep(10)
        buy_count += 1
        total_cost += add_to_cart_cost
        log(f"Purchased {buy_count} of {MAX_BUY_COUNT} via Add to Cart at: ${add_to_cart_cost}")
        continue

log(f"Purchased {buy_count} item(s) at a total cost of: {total_cost}.")
