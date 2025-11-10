import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib
from .utils import get_logger, render_template
from pathlib import Path
import numpy as np

logger = get_logger()

def train(data_path, model_path, test_size=0.2):
    df = pd.read_csv(data_path, parse_dates=["date"])
    # features and target: predict next-day pm25_mean (shifted)
    df = df.sort_values(["location","date"])
    df["pm25_next_day"] = df.groupby("location")["pm25_mean"].shift(-1)
    df = df.dropna(subset=["pm25_next_day"])
    features = ["pm25_mean","pm25_max","pm10_mean","no2_mean","so2_mean","temp_mean","humidity_mean","wind_speed_mean","precip_sum","pm25_roll3","pm25_roll7","pm25_trend_3"]
    df.fillna(0, inplace=True)
    X = df[features]
    y = df["pm25_next_day"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    mse = mean_squared_error(y_test, preds)
    rmse = mse ** 0.5
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    logger.info(f"Model saved to {model_path}. RMSE: {rmse:.3f}")
    return {"model_path": model_path, "rmse": float(rmse)}

def predict_today(model_path, output_path):
    model = joblib.load(model_path)
    processed = pd.read_csv("artifacts/data/processed.csv", parse_dates=["date"])
    # use latest record per location
    last = processed.sort_values("date").groupby("location").tail(1)
    features = ["pm25_mean","pm25_max","pm10_mean","no2_mean","so2_mean","temp_mean","humidity_mean","wind_speed_mean","precip_sum","pm25_roll3","pm25_roll7","pm25_trend_3"]
    X = last[features].fillna(0)
    preds = model.predict(X)
    out = last[["location","date"]].copy()
    out["pm25_pred_next_day"] = preds
    # classify air quality category (simple)
    def aqi_category(pm25):
        if pm25 <= 12:
            return "Good"
        if pm25 <= 35.4:
            return "Moderate"
        if pm25 <= 55.4:
            return "Unhealthy for Sensitive Groups"
        if pm25 <= 150.4:
            return "Unhealthy"
        if pm25 <= 250.4:
            return "Very Unhealthy"
        return "Hazardous"
    out["aqi_category"] = out["pm25_pred_next_day"].apply(aqi_category)
    output_path = render_template(output_path)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_path, index=False)
    logger.info(f"Predictions saved to {output_path}")
    return str(output_path)
