# src/streamlit_actions.py (or directly inside src/dashboard.py)
import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime
import os

# Config from secrets
GH_TOKEN = st.secrets.get("GH_TRIGGER_TOKEN")
OWNER = st.secrets.get("GITHUB_OWNER")
REPO = st.secrets.get("GITHUB_REPO")
WORKFLOW_FILE = st.secrets.get("WORKFLOW_FILE", "pipeline-commit.yml")
BRANCH = st.secrets.get("BRANCH", "main")
RAW_BASE = st.secrets.get("RAW_BASE", "https://raw.githubusercontent.com")

HEADERS = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}

def trigger_workflow():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches"
    payload = {"ref": BRANCH}
    r = requests.post(url, json=payload, headers=HEADERS)
    return r.status_code, r.text

def get_latest_workflow_run():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows/{WORKFLOW_FILE}/runs"
    r = requests.get(url, headers=HEADERS, params={"per_page": 5})
    if r.status_code != 200:
        return None
    runs = r.json().get("workflow_runs", [])
    if not runs:
        return None
    return runs[0]  # latest run

def wait_for_run_completion(poll_interval=5, timeout=600):
    """Poll the workflow runs until latest is completed or timeout (seconds)."""
    start = time.time()
    last_seen_id = None
    while True:
        run = get_latest_workflow_run()
        if not run:
            time.sleep(poll_interval)
            if time.time() - start > timeout:
                return None
            continue

        run_id = run["id"]
        status = run["status"]        # "in_progress"/"completed"/"queued"
        conclusion = run.get("conclusion")  # "success"/"failure"/None

        # show progress to user
        st.text(f"Workflow run {run_id} status={status} conclusion={conclusion}")

        if status == "completed":
            return run
        if time.time() - start > timeout:
            return run
        time.sleep(poll_interval)

def fetch_latest_prediction_csv(path_in_repo="artifacts/predictions/latest.csv"):
    """
    Fetches the latest CSV from the main branch raw URL.
    Make sure pipeline writes to exactly this path when committing.
    """
    raw_url = f"{RAW_BASE}/{OWNER}/{REPO}/{BRANCH}/{path_in_repo}"
    r = requests.get(raw_url)
    if r.status_code == 200:
        # load to pandas
        import io
        return pd.read_csv(io.StringIO(r.text))
    else:
        st.error(f"Could not fetch raw file: {raw_url} (status {r.status_code})")
        return None

# Streamlit UI snippet you can paste into src/dashboard.py
def streamlit_run_pipeline_ui():
    st.header("Pipeline Control")

    if st.button("Run pipeline now (GitHub Actions)"):
        with st.spinner("Triggering workflow..."):
            scode, txt = trigger_workflow()
            if scode in (204, 201, 200):
                st.success("Workflow triggered successfully. Waiting for completion...")
            else:
                st.error(f"Trigger failed: {scode} {txt}")
                return

        # Poll for completion (blocks UI for short time; ok for a few minutes)
        run = wait_for_run_completion(poll_interval=6, timeout=900)  # wait up to 15 min
        if not run:
            st.warning("No workflow run found or timed out.")
            return

        run_url = run.get("html_url")
        conclusion = run.get("conclusion")
        st.write(f"Run finished: {run_url} — conclusion: {conclusion}")

        if conclusion == "success":
            st.success("Pipeline succeeded — fetching latest predictions from repo.")
            df = fetch_latest_prediction_csv()
            if df is not None:
                st.dataframe(df.head(200))
        else:
            st.error("Pipeline run failed. Check Actions log: " + run_url)
