# ADD ROTATING PROXIES?

from seleniumbase import SB
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from seleniumbase.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time
import json

URL = "https://www.glassdoor.com/Job/index.htm"
JOB_NAME = "rust"
LOCATION = "berlin"


def scraper(url, job_name, location):
    print("[INFO] Starting scraper...")
    with SB(uc=True, headless=True) as sb:
        print("[INFO] Opening URL...")
        sb.uc_open_with_reconnect(url, 8)

        # Accept cookies
        try:
            sb.click('//*[@id="onetrust-accept-btn-handler"]')
            print("[INFO] Cookies accepted.")
        except (TimeoutException, NoSuchElementException):
            print("[INFO] No cookie dialog found.")

        # Fill in the input fields
        print(f"[INFO] Entering job name: {job_name}")
        sb.click('//*[@id="searchBar-jobTitle"]')
        sb.type('//*[@id="searchBar-jobTitle"]', job_name)

        print(f"[INFO] Entering location: {location}")
        sb.click('//*[@id="searchBar-location"]')
        sb.type('//*[@id="searchBar-location"]', location + Keys.ENTER)

        # Handle captcha
        try:
            sb.uc_gui_click_captcha()
            print("[INFO] CAPTCHA clicked (if present).")
        except Exception:
            print("[INFO] CAPTCHA not found or not needed. Continuing...")

        # Scroll the page and click the show more button
        print("[INFO] Clicking page header to focus.")
        sb.click('//*[@id="left-column"]/div[1]/span/div/h1')

        first_show_more_clicked = False

        while True:
            print("[INFO] Scrolling to bottom of page...")
            sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            try:
                sb.wait_for_element_visible('//*[@id="left-column"]/div[2]/div/div/button', timeout=5)
                sb.click('//*[@id="left-column"]/div[2]/div/div/button')
                print("[INFO] Clicked 'Show More' button.")
                time.sleep(2.5)

                if not first_show_more_clicked:
                    try:
                        sb.click('button.CloseButton')
                        print("[INFO] Clicked CloseButton after first Show More.")
                    except (TimeoutException, NoSuchElementException):
                        print("[INFO] No CloseButton found after first Show More.")
                    first_show_more_clicked = True

            except (TimeoutException, NoSuchElementException):
                print("[INFO] 'Show More' button not found or no longer clickable. Reached end of list.")
                break

        print("[INFO] Scrolling and pagination complete.")
        return sb.get_page_source()


def parse_jobs(page_source):
    print("[INFO] Parsing page source with BeautifulSoup...")
    soup = BeautifulSoup(page_source, "html.parser")

    job_cards = soup.find_all("div", class_="jobCard JobCard_jobCardContent__JQ5Rq JobCardWrapper_easyApplyLabelNoWrap__PtpgT")

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

    return jobs


if __name__ == "__main__":
    html_source = scraper(URL, JOB_NAME, LOCATION)
    jobs = parse_jobs(html_source)

    with open("jobs.json", "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)

    print(f"[INFO] Saved {len(jobs)} jobs to jobs.json.")
