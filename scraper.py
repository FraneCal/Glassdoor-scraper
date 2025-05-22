import os
import time
import pandas as pd
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from dotenv import load_dotenv

# load_dotenv()
#
# # 2Captcha Proxy Configuration
# TWOCAPTCHA_USERNAME = os.getenv('TWOCAPTCHA_USERNAME')
# TWOCAPTCHA_PASSWORD = os.getenv('TWOCAPTCHA_PASSWORD')
# PROXY_DNS = os.getenv('PROXY_DNS')


class MondayMarketPlaceScraper():
    def __init__(self) -> None:
        '''Initializes Selenium WebDriver and sets up proxy'''
        print("[INFO] Initializing WebDriver...")
        # self.proxy_url = self.get_proxy()
        self.setup_driver()

    # def get_proxy(self):
    #     """
    #     Returns a dictionary with proxy credentials formatted for HTTP/S use.
    #     """
    #     proxy_url = f"http://{TWOCAPTCHA_USERNAME}:{TWOCAPTCHA_PASSWORD}@{PROXY_DNS}"
    #     return proxy_url
    #
    # def check_ip(self, proxy):
    #     """
    #     Returns the current external IP and country using the configured proxy.
    #     """
    #     print("[INFO] Checking proxy IP address...")
    #     try:
    #         response = requests.get("http://ip-api.com/json", proxies=proxy, timeout=10)
    #         ip_data = response.json()
    #         ip_address = ip_data.get('query', 'Unknown')
    #         country = ip_data.get('country', 'Unknown')
    #         print(f"[INFO] Current Proxy IP: {ip_address} ({country})")
    #         return ip_address, country
    #     except requests.exceptions.RequestException:
    #         print("[WARNING] Failed to fetch IP address. Proxy might be blocked!")
    #         return "Failed", "Unknown"

    def setup_driver(self):
        '''Configures the Selenium WebDriver (Chrome) with proxy'''
        self.options = Options()
        # self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        # self.options.add_argument(f'--proxy-server={self.proxy_url}')
        try:
            self.driver = webdriver.Chrome(options=self.options)
            self.driver.maximize_window()
            print("[INFO] WebDriver initialized successfully with proxy.")
        except Exception as e:
            print(f"[ERROR] Failed to initialize WebDriver: {e}")
            raise

    def scrolling_and_pagination(self, URL):
        '''Automates scrolling and paginating through search results'''
        print(f"[INFO] Navigating to URL: {URL}")
        try:
            self.driver.get(URL)
            print("[INFO] Page loaded. Waiting for main element...")

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#left-column > div.JobsList_wrapper__EyUF6 > ul"))
            )

            # Accept cookies
            try:
                accept_cookies = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]')))
                accept_cookies.click()
            except TimeoutException:
                print("No accept cookies button found.")

            time.sleep(2)

            # Log in to account
            log_in_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="SignInButton"]/div')))
            log_in_button.click()

            email_field = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="fishbowlCoRegEmail"]')))
            email_field.click()
            email_field.send_keys("fcalus00@fesb.hr")

            continue_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[7]/div[2]/div[2]/div[1]/div/div[2]/div/div/div/div/div/div/form/div[2]/div/button')))
            continue_button.click()

            password_field = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="fishbowlCoRegPassword"]')))
            password_field.click()
            password_field.send_keys("In71948N.")

            sign_in_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[7]/div[2]/div[2]/div[1]/div/div[2]/div/div/div/div/div/div/form/div[2]/div/button')))
            sign_in_button.click()

            time.sleep(3)

            # Scroll page to the bottom
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            while True:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Adjust if necessary for content to load

                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    print("[INFO] Reached end of page. No more content to load.")
                    break
                last_height = new_height
                print("[INFO] Scrolled further down...")

            print("[INFO] Scrolling and pagination complete.")

        except TimeoutException:
            print(f"[WARNING] Timeout while loading page or waiting for element at {URL}")
        except Exception as e:
            print(f"[ERROR] Unexpected error during scrolling: {e}")



if __name__ == "__main__":
    URL = "https://www.glassdoor.com/Job/luxembourg-java-jobs-SRCH_IL.0,10_IC2941423_KO11,15.htm"
    print("[INFO] Script started.")

    scraper = MondayMarketPlaceScraper()
    # proxy_ip, country = scraper.check_ip({"http": scraper.proxy_url, "https": scraper.proxy_url})

    try:
        scraper.scrolling_and_pagination(URL)
        # scraper.log_visit(URL, proxy_ip, country)
    finally:
        scraper.driver.quit()
        print("[INFO] WebDriver closed. Script finished.")
