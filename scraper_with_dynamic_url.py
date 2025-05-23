import time
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from region_codes import REGION_CODES

# Job name and location
JOB_NAME = "python"
LOCATION = "belgium"

class MondayMarketPlaceScraper():
    def __init__(self) -> None:
        print("[INFO] Initializing WebDriver...")
        self.setup_driver()

    def setup_driver(self):
        self.options = Options()
        # self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        try:
            self.driver = webdriver.Chrome(options=self.options)
            self.driver.maximize_window()
            print("[INFO] WebDriver initialized.")
        except Exception as e:
            print(f"[ERROR] Failed to initialize WebDriver: {e}")
            raise

    def generate_glassdoor_url(self, job_title: str, location: str) -> str:
        job = job_title.lower().replace(" ", "-")
        loc = location.lower().replace(" ", "-")

        region_code = REGION_CODES.get(loc)
        if not region_code:
            raise ValueError(f"[ERROR] Region code not found for: {location}")

        il_start = 0
        il_end = len(loc)
        ko_start = il_end + 1
        ko_end = ko_start + len(job)

        return (f"https://www.glassdoor.com/Job/"
                f"{loc}-{job}-jobs-SRCH_IL.{il_start},{il_end}_{region_code}_KO{ko_start},{ko_end}.htm")

    def scrolling_and_pagination(self, job_title, location):
        url = self.generate_glassdoor_url(job_title, location)
        print(f"[INFO] Navigating to URL: {url}")
        try:
            self.driver.get(url)

            # Accept cookies
            try:
                accept_cookies = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                )
                accept_cookies.click()
                print("[INFO] Accepted cookies.")
            except TimeoutException:
                print("[INFO] No cookie dialog found.")

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
                    print("[INFO] 'Show More' button not found. Reached end of list.")
                    break

            print("[INFO] Scrolling and pagination complete.")
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")

        self.bs4_initialization()

    def bs4_initialization(self):
        self.page_source = self.driver.page_source
        self.soup = BeautifulSoup(self.page_source, "html.parser")
        self.scrape_jobs()

    def scrape_jobs(self):
        job_cards = self.soup.find_all("div", class_="jobCard JobCard_jobCardContent__JQ5Rq JobCardWrapper_easyApplyLabelNoWrap__PtpgT")
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

            if job_data:
                jobs.append(job_data)

        with open("jobs.json", "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)

        print(f"[INFO] Saved {len(jobs)} jobs to jobs.json.")

if __name__ == "__main__":
    print("[INFO] Script started.")
    scraper = MondayMarketPlaceScraper()

    try:
        scraper.scrolling_and_pagination(JOB_NAME, LOCATION)
    finally:
        scraper.driver.quit()
        print("[INFO] WebDriver closed. Script finished.")
