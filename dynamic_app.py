import streamlit as st
import pandas as pd
import json
import subprocess
import os

# ---------- CONFIG ----------
JOBS_FILE = "jobs.json"
SCRAPER_FILE = "scraper.py"


# ---------- LOAD JOB DATA ----------
def load_jobs(filepath=JOBS_FILE):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


# ---------- WRITE SCRAPER PARAMS TO ENV ----------
def set_scraper_params(job_name, location):
    with open(".env", "w") as f:
        f.write(f"JOB_NAME={job_name}\n")
        f.write(f"LOCATION={location}\n")


# ---------- CALL SCRAPER ----------
def run_scraper(job_name, location):
    set_scraper_params(job_name, location)
    try:
        subprocess.run(["python", SCRAPER_FILE], check=True)
        return True
    except subprocess.CalledProcessError as e:
        st.error("Scraping failed. Check logs.")
        return False


# ---------- MAIN APP ----------
def main():
    st.set_page_config(page_title="Job Listings", layout="wide")
    st.title("📋 Glassdoor Job Scraper")

    jobs = []

    # --- Input Form ---
    with st.form("scrape_form"):
        job_name = st.text_input("🔍 Job Name", value="", placeholder="e.g. javascript")
        location = st.text_input("📍 Location", value="", placeholder="e.g. spain")
        submitted = st.form_submit_button("🚀 Scrape")

        if submitted:
            if not job_name or not location:
                st.warning("Please enter both Job Name and Location.")
            else:
                with st.spinner("Scraping jobs..."):
                    success = run_scraper(job_name, location)
                    if success:
                        st.success("Scraping complete. Displaying jobs:")
                        jobs = load_jobs()

    # --- Refresh Button ---
    if st.button("🔁 Refresh Job Data"):
        jobs = load_jobs()
        st.success("Data refreshed!")

    # --- Show Table If Jobs Are Available ---
    if jobs:
        df = pd.DataFrame(jobs)

        # Filter by Location
        all_locations = sorted(df["location"].dropna().unique())
        selected_location = st.selectbox("📍 Filter by Location", options=["All"] + all_locations)

        filtered_df = df.copy()
        if selected_location != "All":
            filtered_df = filtered_df[filtered_df["location"] == selected_location]

        st.markdown("### Filtered Results")
        st.write(f"Total jobs: {len(filtered_df)}")
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.info("No job data to display yet. Please run a scrape.")


if __name__ == "__main__":
    main()
