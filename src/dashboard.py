# src/dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import glob
import altair as alt
from datetime import datetime
import time

# Page config (single call)
st.set_page_config(page_title="Air Quality Dashboard", layout="wide")

# ---- Manual refresh button (safe, no blocking) ----
# Use experimental_rerun if available; otherwise use a query-param trick as a fallback.
if st.sidebar.button("Refresh dashboard now"):
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    else:
        # fallback: modify query params to force Streamlit to re-run the script
        st.experimental_set_query_params(_refresh=int(time.time()))

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"
PROCESSED = ARTIFACTS / "data" / "processed.csv"
PRED_DIR = ARTIFACTS / "predictions"

# ---------- helpers ----------
AQI_BREAKPOINTS = [
    (0, 12, "Good"),
    (12.1, 35.4, "Moderate"),
    (35.5, 55.4, "Unhealthy for Sensitive Groups"),
    (55.5, 150.4, "Unhealthy"),
    (150.5, 250.4, "Very Unhealthy"),
    (250.5, 500, "Hazardous"),
]

def aqi_category(pm25):
    for low, high, name in AQI_BREAKPOINTS:
        if low <= pm25 <= high:
            return name
    return "Unknown"

def latest_prediction_file():
    files = sorted(glob.glob(str(PRED_DIR / "prediction_*.csv")))
    return files[-1] if files else None

def load_processed():
    if not PROCESSED.exists():
        return None
    df = pd.read_csv(PROCESSED, parse_dates=["date"])
    # ensure date column dtype is date (not datetime)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df

def load_prediction(path):
    if path is None:
        return None
    df = pd.read_csv(path, parse_dates=["date"])
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df

# optional static lat/lon mapping for simple map (edit coordinates to match real locations)
DEFAULT_LOCATION_COORDS = {
    "Banglore": (28.7041, 77.1025),
    "Tokyo": (12.9716, 77.5946),
    "Belfest": (19.0760, 72.8777),
    "zurich": (13.0827, 80.2707),
    "Hallstat": (22.5726, 88.3639),
}

# ---------- layout ----------
st.title("Air Quality Monitoring & Prediction — Dashboard")
st.caption("Local, YAML-driven pipeline outputs (simulated data)")

processed = load_processed()
pred_file = latest_prediction_file()
prediction = load_prediction(pred_file)

col1, col2 = st.columns([2, 1])

with col2:
    st.markdown("### Latest prediction file")
    if pred_file:
        st.write(Path(pred_file).name)
        st.download_button("Download latest prediction CSV", data=open(pred_file, "rb"), file_name=Path(pred_file).name)
    else:
        st.info("No prediction file found. Run the pipeline to generate predictions.")

    st.markdown("### Quick stats")
    if processed is not None and not processed.empty:
        latest_date = processed["date"].max()
        st.write("Data last processed for:", latest_date)
        st.write("Locations:", processed["location"].nunique())
        st.write("Days of data:", processed["date"].nunique())
    else:
        st.info("No processed data found. Run the pipeline to create processed.csv")

with col1:
    if processed is None:
        st.warning("No processed data available. Run the pipeline (python -m src.pipeline_runner) first.")
    else:
        # Location selector
        locations = sorted(processed["location"].unique())
        sel_loc = st.selectbox("Select location", options=locations, index=0)

        # Date range
        min_date = processed["date"].min()
        max_date = processed["date"].max()
        date_range = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

        # filter data
        mask = (processed["location"] == sel_loc) & (processed["date"] >= date_range[0]) & (processed["date"] <= date_range[1])
        subset = processed[mask].copy()

        st.markdown(f"### PM2.5 trend for {sel_loc}")
        if subset.empty:
            st.info("No rows for selection.")
        else:
            # line chart of pm25_mean and predicted next-day if available
            chart_df = subset[["date", "pm25_mean", "pm25_max", "pm25_roll3"]].melt(id_vars=["date"], var_name="series", value_name="value")
            line = alt.Chart(chart_df).mark_line(point=True).encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("value:Q", title="PM2.5"),
                color="series:N",
                tooltip=["date:T", "series:N", "value:Q"]
            ).interactive()
            # new API: use width='stretch' instead of deprecated use_container_width
            st.altair_chart(line, width="stretch")

            # show last observed and predicted (if prediction exists)
            last_obs = subset.sort_values("date").tail(1).iloc[0]
            st.write("Latest observed PM2.5 (mean):", round(last_obs["pm25_mean"], 2))
            if prediction is not None:
                pred_row = prediction[prediction["location"] == sel_loc]
                if not pred_row.empty:
                    pred_val = float(pred_row["pm25_pred_next_day"].iloc[0])
                    st.write("Predicted PM2.5 next day:", round(pred_val, 2), " — ", aqi_category(pred_val))
                else:
                    st.info("No prediction for this location in latest file.")

        # show table of recent processed rows for location
        st.markdown("Recent processed rows")
        st.dataframe(subset.sort_values("date", ascending=False).head(10))

# ---------- global predictions table ----------
st.markdown("## Latest Predictions — All locations")
if prediction is None:
    st.info("No predictions available. Run pipeline to generate predictions.")
else:
    # decorate with AQI
    prediction["aqi_category"] = prediction["pm25_pred_next_day"].apply(aqi_category)
    st.dataframe(prediction.sort_values("pm25_pred_next_day", ascending=False).reset_index(drop=True))

    # show locations needing attention
    warn = prediction[prediction["aqi_category"].isin(["Unhealthy","Very Unhealthy","Hazardous","Unhealthy for Sensitive Groups"])]
    st.markdown("### Locations needing attention (Unhealthy or worse)")
    if warn.empty:
        st.success("No locations currently in unhealthy categories based on predictions.")
    else:
        st.table(warn[["location", "pm25_pred_next_day", "aqi_category"]])

    # small map (approx) using default coords (if available)
    coords = []
    for _, row in prediction.iterrows():
        loc = row["location"]
        if loc in DEFAULT_LOCATION_COORDS:
            lat, lon = DEFAULT_LOCATION_COORDS[loc]
            coords.append({"lat": lat, "lon": lon, "pm25": row["pm25_pred_next_day"], "loc": loc})
    if coords:
        st.markdown("### Map (approx locations)")
        map_df = pd.DataFrame(coords)
        map_df = map_df.rename(columns={"lat": "lat", "lon": "lon"})
        st.map(map_df[["lat", "lon"]])

# ---------- model metrics & history ----------
st.markdown("## Model & history")
# show simple model metrics file if exists in artifacts/reports (you can save metrics there in model.train)
report_files = sorted(glob.glob(str(ARTIFACTS / "reports" / "*.csv")) + glob.glob(str(ARTIFACTS / "reports" / "*.json")))
if report_files:
    st.write("Recent model report files:")
    for f in report_files[-5:]:
        st.write("-", Path(f).name)
else:
    st.info("No model reports found. Consider saving model metrics in artifacts/reports/ after training.")

st.markdown("---")
st.caption(f"Dashboard last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
