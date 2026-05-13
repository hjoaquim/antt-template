"""One-shot batch scoring for the ForecastTrafficVolume model.

Runs once before Day 3 to produce fact_forecast_monthly.csv. Trainees
read this file in the docs but do not run it during the lab.

The output CSV is committed to the day-3-starter branch and downloaded
by trainees as the input to the Power BI lab.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import mlflow
import pandas as pd
from mlflow.client import MlflowClient
from sqlalchemy.engine import Engine

from ml.features import FEATURE_COLS, build_engine, build_features

MODEL_NAME = "ForecastTrafficVolume"
ALIAS = "production"
MODEL_URI = f"models:/{MODEL_NAME}@{ALIAS}"
HOLDOUT_START = pd.Timestamp("2019-07-01")
HOLDOUT_END = pd.Timestamp("2019-12-01")

OUTPUT_COLUMNS = [
    "plaza_key",
    "direction",
    "vehicle_key",
    "date_key",
    "volume_forecast",
    "model_version",
    "model_uri",
]


def _holdout_features(engine: Engine) -> pd.DataFrame:
    """Slice build_features() down to the holdout window."""
    df = build_features(engine=engine)
    mask = (df["month_start"] >= HOLDOUT_START) & (df["month_start"] <= HOLDOUT_END)
    return df.loc[mask].copy()


def _resolve_production_version(client: MlflowClient) -> int:
    return int(client.get_model_version_by_alias(MODEL_NAME, ALIAS).version)


def _load_key_lookups(engine: Engine) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load surrogate-key lookups from Gold dimensions.

    Note: plaza_key and vehicle_key are UUID hashes from the Gold schema.
    date_key is derived as an integer YYYYMMDD from month_start (the
    Gold dim_date.date_key is also a UUID, but YYYYMMDD integers are the
    standard BI-tool-friendly surrogate for dates and are what the smoke
    tests expect).
    """
    plazas = pd.read_sql(
        "select plaza_key, plaza_name from gold.dim_plaza", engine,
    )
    vehicles = pd.read_sql(
        "select vehicle_key, vehicle_type from gold.dim_vehicle", engine,
    )
    dates = pd.read_sql(
        "select month_start from gold.dim_date", engine,
        parse_dates=["month_start"],
    )
    # Derive integer YYYYMMDD key — standard for BI tools and expected by tests.
    dates["date_key"] = dates["month_start"].dt.strftime("%Y%m%d").astype(int)
    return plazas, vehicles, dates


def score(output_path: Optional[Path] = None) -> Path:
    """Predict the holdout window, write the CSV, return the output path."""
    output_path = (
        Path(output_path)
        if output_path is not None
        else Path("powerbi/data/fact_forecast_monthly.csv")
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    engine = build_engine()
    client = MlflowClient()
    version = _resolve_production_version(client)
    model = mlflow.sklearn.load_model(MODEL_URI)

    features = _holdout_features(engine)
    predictions = model.predict(features[FEATURE_COLS])

    plazas, vehicles, dates = _load_key_lookups(engine)

    out = features[["plaza_name", "vehicle_type", "direction", "month_start"]].copy()
    out["volume_forecast"] = predictions.round().astype(int)
    out = out.merge(plazas, on="plaza_name", how="inner")
    out = out.merge(vehicles, on="vehicle_type", how="inner")
    out = out.merge(dates, on="month_start", how="inner")
    out["model_version"] = version
    out["model_uri"] = MODEL_URI
    out = out[OUTPUT_COLUMNS]

    out.to_csv(output_path, index=False)
    return output_path


if __name__ == "__main__":
    path = score()
    print(f"Wrote {path}")
