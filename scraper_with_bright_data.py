import os
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.webdriver import Remote, ChromeOptions
from dotenv import load_dotenv
import json

# load_dotenv()

# 2Captcha Proxy Configuration
TWOCAPTCHA_USERNAME = ""
TWOCAPTCHA_PASSWORD = ""
PROXY_DNS = ""

# Job name and location
JOB_NAME = "javascript"
LOCATION = "germany"

# Bright data
AUTH = ""
SBR_WEBDRIVER = f'https://{AUTH}@brd.superproxy.io:9515'

class MondayMarketPlaceScraper():
    def __init__(self):
        print("[INFO] Connecting to Bright Data Scraping Browser...")
        self.sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, "goog", "chrome")
        self.driver = Remote(self.sbr_connection, options=ChromeOptions())
        print("[INFO] Connected to remote browser.")

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
        '''Continuously scrolls and clicks "Show More" until the button is gone'''
        print(f"[INFO] Navigating to URL: {URL}")
        try:
            self.driver.get(URL)
            # print("[INFO] Page loaded. Waiting for job list container...")
            # WebDriverWait(self.driver, 10).until(
            #     EC.presence_of_element_located((By.CSS_SELECTOR, "#left-column > div.JobsList_wrapper__EyUF6 > ul"))
            # )

            # Accept cookies
            try:
                accept_cookies = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                )
                accept_cookies.click()
                print("[INFO] Accepted cookies.")
            except TimeoutException:
                print("[INFO] No cookie dialog found.")

            # # Job name and location
            job_field = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="searchBar-jobTitle"]'))
            )
            job_field.click()
            job_field.send_keys(JOB_NAME)
            print("[INFO] Job name added.")

            location_field = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="searchBar-location"]'))
            )
            location_field.click()
            location_field.send_keys(LOCATION)
            location_field.send_keys(Keys.ENTER)
            print("[INFO] Location added.")

            # Wait and solve CAPTCHA if needed (Bright Data handles many automatically)
            try:
                print("[INFO] Waiting for CAPTCHA (if any)...")
                solve_res = self.driver.execute(
                    "executeCdpCommand",
                    {"cmd": "Captcha.waitForSolve", "params": {"detectTimeout": 5000}},
                )
                print("[INFO] CAPTCHA solve status:", solve_res["value"]["status"])
            except Exception as e:
                print("[INFO] No CAPTCHA or already bypassed.")

            # Click the job list before scrolling
            try:
                job_list = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="left-column"]/div[1]/span/div/h1'))
                )
                job_list.click()
                print("[INFO] Clicked job list.")
            except TimeoutException:
                print("[INFO] Left menu not found or already opened.")

            while True:
                # Scroll to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

                try:
                    show_more_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, '//*[@id="left-column"]/div[2]/div/div/button'))
                    )
                    show_more_btn.click()
                    print("[INFO] Clicked 'Show More'.")
                    time.sleep(2.5)
                except TimeoutException:
                    print("[INFO] 'Show More' button not found or no longer clickable. Reached end of list.")
                    break

            print("[INFO] Scrolling and pagination complete.")

        except TimeoutException:
            print(f"[WARNING] Timeout while loading page or waiting for element at {URL}")
        except Exception as e:
            print(f"[ERROR] Unexpected error during scrolling: {e}")

        # After loading the page, initialize BeautifulSoup for further scraping
        self.bs4_initialization()

    def bs4_initialization(self):
        '''Fetches the page source using Selenium and initializes BeautifulSoup for parsing the HTML content.'''
        self.page_source = self.driver.page_source

        self.soup = BeautifulSoup(self.page_source, "html.parser")

        # Scrape job listings
        self.scrape_jobs()

    def scrape_jobs(self):
        job_cards = self.soup.find_all("div",class_="jobCard JobCard_jobCardContent__JQ5Rq JobCardWrapper_easyApplyLabelNoWrap__PtpgT")

        jobs = []

        for card in job_cards:
            job_data = {}

            title_tag = card.find("a", class_="JobCard_jobTitle__GLyJ1")
            if title_tag:
                job_data["title"] = title_tag.getText(strip=True)
                job_data["link"] = title_tag.get("href")

            location_tag = card.find("div", class_="JobCard_location__Ds1fM")
            if location_tag:
                job_data["location"] = location_tag.getText(strip=True)

            employeer_tag = card.find("div", class_="EmployerProfile_profileContainer__63w3R EmployerProfile_compact__28h9t")
            if employeer_tag:
                job_data["employeer"] = employeer_tag.getText(strip=True)

            short_description_tag = card.find("div", class_="JobCard_jobDescriptionSnippet__l1tnl")
            if short_description_tag:
                job_data["short description"] = short_description_tag.getText(strip=True)

            if job_data:  # Only add non-empty entries
                jobs.append(job_data)

        # Save to JSON
        with open("jobs.json", "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)

        print(f"[INFO] Saved {len(jobs)} jobs to jobs.json.")

if __name__ == "__main__":
    # URL = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={JOB_NAME.lower()}&locT=C&locId=&locKeyword={LOCATION.lower()}"
    URL = "https://www.glassdoor.com/Job/index.htm"
    print("[INFO] Script started.")

    scraper = MondayMarketPlaceScraper()
    # proxy_ip, country = scraper.check_ip({"http": scraper.proxy_url, "https": scraper.proxy_url})

    try:
        scraper.scrolling_and_pagination(URL)
        # scraper.log_visit(URL, proxy_ip, country)
    finally:
      try:
          scraper.driver.quit()
      except Exception as e:
          print(f"[WARNING] Error closing WebDriver: {e}")
      print("[INFO] WebDriver closed. Script finished.")
