import time
import json
from bs4 import BeautifulSoup
from seleniumbase import BaseCase
from selenium.webdriver.chrome.options import Options

# Job name and location
JOB_NAME = "javascript"
LOCATION = "spain"

class MondayMarketPlaceScraper(BaseCase):

    def setUp(self):
        # Configure Chrome options for stealth
        opts = Options()
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--disable-infobars")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--profile-directory=Default")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-features=NetworkService")
        opts.add_argument("--window-size=1920,1080")
        # You can add more stealth-related args if needed

        self.set_chrome_options(opts)
        super().setUp()

    def scrolling_and_pagination(self, URL):
        print(f"[INFO] Navigating to URL: {URL}")
        self.open(URL)

        # Remove webdriver flag via JS
        self.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # Accept cookies if present
        try:
            self.wait_for_element("#onetrust-accept-btn-handler", timeout=5)
            self.click("#onetrust-accept-btn-handler")
            print("[INFO] Accepted cookies.")
        except Exception:
            print("[INFO] No cookie dialog found.")

        # Fill job name field
        self.wait_for_element('//*[@id="searchBar-jobTitle"]', by="xpath", timeout=5)
        self.click('//*[@id="searchBar-jobTitle"]', by="xpath")
        self.send_keys('//*[@id="searchBar-jobTitle"]', JOB_NAME, by="xpath")

        # Fill location field
        self.wait_for_element('//*[@id="searchBar-location"]', by="xpath", timeout=5)
        self.click('//*[@id="searchBar-location"]', by="xpath")
        self.send_keys('//*[@id="searchBar-location"]', LOCATION, by="xpath")
        self.send_keys('//*[@id="searchBar-location"]', "\n", by="xpath")  # Press Enter

        # Try clicking job list header if exists
        try:
            self.wait_for_element('//*[@id="left-column"]/div[1]/span/div/h1', by="xpath", timeout=5)
            self.click('//*[@id="left-column"]/div[1]/span/div/h1', by="xpath")
            print("[INFO] Clicked job list.")
        except Exception:
            print("[INFO] Left menu not found or already opened.")

        while True:
            self.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            try:
                self.wait_for_element('//*[@id="left-column"]/div[2]/div/div/button', by="xpath", timeout=5)
                self.click('//*[@id="left-column"]/div[2]/div/div/button', by="xpath")
                print("[INFO] Clicked 'Show More'.")
                time.sleep(2.5)
            except Exception:
                print("[INFO] 'Show More' button not found or no longer clickable. Reached end of list.")
                break

        print("[INFO] Scrolling and pagination complete.")

        # Parse page source with BeautifulSoup
        self.bs4_initialization()

    def bs4_initialization(self):
        page_source = self.get_page_source()
        self.soup = BeautifulSoup(page_source, "html.parser")
        self.scrape_jobs()

    def scrape_jobs(self):
        job_cards = self.soup.find_all("div", class_="jobCard JobCard_jobCardContent__JQ5Rq JobCardWrapper_easyApplyLabelNoWrap__PtpgT")

        jobs = []

        for card in job_cards:
            job_data = {}

            title_tag = card.find("a", class_="JobCard_jobTitle__GLyJ1")
            if title_tag:
                job_data["title"] = title_tag.get_text(strip=True)
                job_data["link"] = title_tag.get("href")

            location_tag = card.find("div", class_="JobCard_location__Ds1fM")
            if location_tag:
                job_data["location"] = location_tag.get_text(strip=True)

            employeer_tag = card.find("div", class_="EmployerProfile_profileContainer__63w3R EmployerProfile_compact__28h9t")
            if employeer_tag:
                job_data["employeer"] = employeer_tag.get_text(strip=True)

            short_description_tag = card.find("div", class_="JobCard_jobDescriptionSnippet__l1tnl")
            if short_description_tag:
                job_data["short description"] = short_description_tag.get_text(strip=True)

            if job_data:
                jobs.append(job_data)

        with open("jobs.json", "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)

        print(f"[INFO] Saved {len(jobs)} jobs to jobs.json.")


if __name__ == "__main__":
    URL = "https://www.glassdoor.com/Job/"
    print("[INFO] Script started.")

    scraper = MondayMarketPlaceScraper()

    try:
        scraper.scrolling_and_pagination(URL)
    finally:
        scraper.quit()  # Close browser cleanly
        print("[INFO] WebDriver closed. Script finished.")
