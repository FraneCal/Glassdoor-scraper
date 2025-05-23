import streamlit as st
import pandas as pd
import json

# Load job data from JSON
def load_jobs(filepath="jobs.json"):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("No job data found. Please run the scraper first.")
        return []

# Streamlit App
def main():
    st.set_page_config(page_title="Job Listings", layout="wide")
    st.title("📋 Glassdoor Job Scraper Results")

    # Load jobs initially
    if "jobs_data" not in st.session_state:
        st.session_state.jobs_data = load_jobs()

    # Refresh button
    if st.button("🔁 Refresh Job Data"):
        st.session_state.jobs_data = load_jobs()

    jobs = st.session_state.jobs_data

    if not jobs:
        st.warning("No jobs found to display.")
        return

    df = pd.DataFrame(jobs)

    # Filter by location only
    all_locations = sorted(df["location"].dropna().unique())
    selected_location = st.selectbox("📍 Filter by Location", options=["All"] + all_locations)

    filtered_df = df.copy()
    if selected_location != "All":
        filtered_df = filtered_df[filtered_df["location"] == selected_location]

    st.markdown("### Filtered Results")
    st.write(f"Total jobs: {len(filtered_df)}")
    st.dataframe(filtered_df, use_container_width=True)

if __name__ == "__main__":
    main()
