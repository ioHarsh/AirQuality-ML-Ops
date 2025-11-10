import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .config import DATA_DIR
from pathlib import Path
import random

def _date_range(days, freq='hourly'):
    end = datetime.now().replace(minute=0, second=0, microsecond=0)
    if freq == "hourly":
        start = end - timedelta(days=days-1)
        rng = pd.date_range(start=start, end=end + timedelta(hours=23), freq='H')  # cover full days
    else:
        start = (end.date() - timedelta(days=days-1))
        rng = pd.date_range(start=start, periods=days, freq='D')
    return rng

def generate_sensor_readings(days=30, locations=5, freq="hourly", out_path=None):
    dates = _date_range(days, freq=freq)
    rows = []
    locations_list = [f"Loc_{i+1}" for i in range(locations)]
    for loc in locations_list:
        # base pollution level varies by location
        base_pm25 = random.uniform(20, 70)
        for ts in dates:
            # simulate diurnal pattern + noise
            hour = ts.hour
            diurnal = 10 * np.sin((hour / 24) * 2 * np.pi)  # rough day-night pattern
            pm25 = max(0, base_pm25 + diurnal + np.random.normal(0, 5))
            pm10 = pm25 * (1.2 + np.random.normal(0, 0.05))
            no2 = max(0, 20 + np.random.normal(0,5) + (pm25/10))
            so2 = max(0, 5 + np.random.normal(0,2))
            rows.append({"timestamp": ts, "location": loc, "pm25": round(pm25,2),
                         "pm10": round(pm10,2), "no2": round(no2,2), "so2": round(so2,2)})
    df = pd.DataFrame(rows)
    out_path = out_path or (DATA_DIR / "sensor_readings.csv")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return str(out_path)

def generate_weather_data(days=30, locations=5, out_path=None):
    # simple weather features correlated with AQI
    dates = _date_range(days, freq='hourly')
    rows = []
    locations_list = [f"Loc_{i+1}" for i in range(locations)]
    for loc in locations_list:
        for ts in dates:
            temp = 15 + 10 * np.sin((ts.timetuple().tm_yday / 365) * 2 * np.pi) + np.random.normal(0,2)
            humidity = np.clip(40 + 20*np.sin((ts.hour/24)*2*np.pi) + np.random.normal(0,5), 5, 100)
            wind_speed = max(0, np.random.normal(3,1.5))
            precipitation = max(0, np.random.exponential(0.1) - 0.05)  # mostly small chance
            rows.append({"timestamp": ts, "location": loc, "temp": round(temp,2),
                         "humidity": round(humidity,1), "wind_speed": round(wind_speed,2),
                         "precip": round(precipitation,3)})
    df = pd.DataFrame(rows)
    out_path = out_path or (DATA_DIR / "weather.csv")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return str(out_path)
