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

with SB(uc=True) as sb:
    sb.uc_open_with_reconnect(URL, 8)

    # Accept cookies
    try:
        sb.click('//*[@id="onetrust-accept-btn-handler"]')
        print("Cookies accepted.")
    except (TimeoutException, NoSuchElementException):
        print("No cookie dialog found.")

    # Fill in the input fields
    sb.click('//*[@id="searchBar-jobTitle"]')
    sb.type('//*[@id="searchBar-jobTitle"]', JOB_NAME)

    sb.click('//*[@id="searchBar-location"]')
    sb.type('//*[@id="searchBar-location"]', LOCATION + Keys.ENTER)

    # Handle captcha
    try:
        sb.uc_gui_click_captcha()
    except Exception as e:
        print("CAPTCHA not found or not needed. Continuing...")

    # Scroll the page and click the show more button
    sb.click('//*[@id="left-column"]/div[1]/span/div/h1')

    first_show_more_clicked = False

    while True:
        # Scroll to bottom using SeleniumBase execute_script
        sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        try:
            # Wait and click "Show More" button using SeleniumBase
            sb.wait_for_element_visible('//*[@id="left-column"]/div[2]/div/div/button', timeout=5)
            sb.click('//*[@id="left-column"]/div[2]/div/div/button')
            print("Clicked 'Show More'.")
            time.sleep(2.5)

            # Click CloseButton only after first Show More click
            if not first_show_more_clicked:
                try:
                    sb.click('button.CloseButton')
                    print("Clicked CloseButton after first Show More.")
                except (TimeoutException, NoSuchElementException):
                    pass
                first_show_more_clicked = True

        except (TimeoutException, NoSuchElementException):
            print("'Show More' button not found or no longer clickable. Reached end of list.")
            break

    print("Scrolling and pagination complete.")

    page_source = sb.get_page_source()

soup = BeautifulSoup(page_source, "html.parser")

job_cards = soup.find_all("div",class_="jobCard JobCard_jobCardContent__JQ5Rq JobCardWrapper_easyApplyLabelNoWrap__PtpgT")

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

print(f"Saved {len(jobs)} jobs to jobs.json.")
