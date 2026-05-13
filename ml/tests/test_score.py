"""Smoke tests for ml/score.py.

Verifies the CSV shape and headers, holdout window, and model identity tagging.
These tests require a live MLflow registry with ForecastTrafficVolume@production.
"""
from pathlib import Path

import pandas as pd


EXPECTED_COLUMNS = [
    "plaza_key",
    "direction",
    "vehicle_key",
    "date_key",
    "volume_forecast",
    "model_version",
    "model_uri",
]


def test_score_writes_csv_with_expected_columns(tmp_path):
    """score.score() writes a CSV with the documented schema."""
    from ml import score

    out = tmp_path / "fact_forecast_monthly.csv"
    score.score(output_path=out)

    df = pd.read_csv(out)
    assert list(df.columns) == EXPECTED_COLUMNS
    assert len(df) > 0


def test_score_holdout_window_only(tmp_path):
    """All output rows fall inside the Jul–Dec 2019 holdout window."""
    from ml import score

    out = tmp_path / "fact_forecast_monthly.csv"
    score.score(output_path=out)

    df = pd.read_csv(out)
    months = pd.to_datetime(df["date_key"].astype(str), format="%Y%m%d").dt.to_period("M")
    assert months.min() == pd.Period("2019-07")
    assert months.max() == pd.Period("2019-12")


def test_score_records_model_identity(tmp_path):
    """Every row carries the model_uri and a non-empty model_version."""
    from ml import score

    out = tmp_path / "fact_forecast_monthly.csv"
    score.score(output_path=out)

    df = pd.read_csv(out)
    assert (df["model_uri"] == "models:/ForecastTrafficVolume@production").all()
    assert df["model_version"].notna().all()
