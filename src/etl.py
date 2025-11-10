import pandas as pd
from pathlib import Path
from .utils import get_logger

logger = get_logger()

def run_etl(sensor_path, weather_path, out_path, agg_freq="daily"):
    # read
    s = pd.read_csv(sensor_path, parse_dates=["timestamp"])
    w = pd.read_csv(weather_path, parse_dates=["timestamp"])
    # merge on nearest timestamp per hour (they align) and location
    df = pd.merge(s, w, on=["timestamp","location"], how="left")
    # create datetime features
    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour
    # aggregate per location per day or per hour
    if agg_freq == "daily":
        agg = df.groupby(["location","date"]).agg(
            pm25_mean=("pm25","mean"),
            pm25_max=("pm25","max"),
            pm10_mean=("pm10","mean"),
            no2_mean=("no2","mean"),
            so2_mean=("so2","mean"),
            temp_mean=("temp","mean"),
            humidity_mean=("humidity","mean"),
            wind_speed_mean=("wind_speed","mean"),
            precip_sum=("precip","sum")
        ).reset_index()
    else:
        agg = df.copy()
        agg = agg.rename(columns={"timestamp":"date"})  # hourly
    # create lag/rolling features per location
    dfs = []
    for loc, g in agg.groupby("location"):
        g = g.sort_values("date")
        # rolling means for pm25
        g["pm25_roll3"] = g["pm25_mean"].rolling(3, min_periods=1).mean()
        g["pm25_roll7"] = g["pm25_mean"].rolling(7, min_periods=1).mean()
        g["pm25_trend_3"] = g["pm25_mean"].diff(3).fillna(0)
        dfs.append(g)
    out = pd.concat(dfs, ignore_index=True)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    logger.info(f"ETL produced {out_path} with {len(out)} rows")
    return str(out_path)
