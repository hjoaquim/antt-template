# Day 3 — Power BI source data

These five CSVs are the entire input to the Day 3 lab. They are pre-computed
so the lab can stay focused on Power BI rather than on pipelines.

All five CSVs join on string surrogate keys (UUID hashes). The relationships
trainees will build in Power BI are:

- `fact_traffic_monthly[plaza_key]   → dim_plaza[plaza_key]`
- `fact_traffic_monthly[vehicle_key] → dim_vehicle[vehicle_key]`
- `fact_traffic_monthly[date_key]    → dim_date[date_key]`
- `fact_forecast_monthly[plaza_key]   → dim_plaza[plaza_key]`
- `fact_forecast_monthly[vehicle_key] → dim_vehicle[vehicle_key]`
- `fact_forecast_monthly[date_key]    → dim_date[date_key]`

## Files

| File                         | Source                                                                                                                     | Grain                                                                                       | Rows  |
|------------------------------|----------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|-------|
| `dim_plaza.csv`              | `gold.dim_plaza` (Day 1 dbt model)                                                                                          | One row per toll plaza                                                                       | 128   |
| `dim_vehicle.csv`            | `gold.dim_vehicle` (Day 1 dbt model)                                                                                        | One row per vehicle category                                                                 | 3     |
| `dim_date.csv`               | `gold.dim_date` (Day 1 dbt model)                                                                                           | One row per month, Jan 2010 – Dec 2019                                                       | 120   |
| `fact_traffic_monthly.csv`   | `gold.fact_traffic_monthly` (Day 1 dbt model)                                                                               | One row per (plaza, direction, vehicle, month)                                               | 59686 |
| `fact_forecast_monthly.csv`  | `ml/score.py` against `models:/ForecastTrafficVolume@production` — see column `model_version` for the exact version used   | One row per (plaza, direction, vehicle, month) — **holdout window only: Jul–Dec 2019**       | 3709  |

## Columns

### `dim_plaza.csv`

| Column           | Type | Notes                                              |
|------------------|------|----------------------------------------------------|
| `plaza_key`      | str  | Surrogate key (UUID hash). Join target for facts.  |
| `plaza_name`     | str  | Display name of the toll plaza.                    |
| `concessionaria` | str  | The concessionaire operating the plaza.            |

### `dim_vehicle.csv`

| Column         | Type | Notes                                              |
|----------------|------|----------------------------------------------------|
| `vehicle_key`  | str  | Surrogate key (UUID hash). Join target for facts.  |
| `vehicle_type` | str  | Vehicle category (e.g. `Moto`, `Passeio`).         |

### `dim_date.csv`

| Column        | Type | Notes                                              |
|---------------|------|----------------------------------------------------|
| `date_key`    | str  | Surrogate key (UUID hash). Join target for facts.  |
| `month_start` | date | First day of the calendar month.                   |
| `year`        | int  | Calendar year.                                     |
| `quarter`     | int  | Calendar quarter (1–4).                            |
| `month`       | int  | Month-of-year (1–12).                              |
| `year_month`  | str  | Convenience label, e.g. `2019-07`.                 |

### `fact_traffic_monthly.csv`

| Column         | Type | Notes                                              |
|----------------|------|----------------------------------------------------|
| `date_key`     | str  | FK → `dim_date.date_key`.                          |
| `plaza_key`    | str  | FK → `dim_plaza.plaza_key`.                        |
| `vehicle_key`  | str  | FK → `dim_vehicle.vehicle_key`.                    |
| `direction`    | str  | Travel direction (e.g. `Norte`, `Sul`).            |
| `volume_total` | int  | Total vehicles crossing the plaza in that month.   |

### `fact_forecast_monthly.csv`

| Column            | Type | Notes                                                                  |
|-------------------|------|------------------------------------------------------------------------|
| `plaza_key`       | str  | FK → `dim_plaza.plaza_key`.                                            |
| `direction`       | str  | Travel direction (e.g. `Norte`, `Sul`).                                |
| `vehicle_key`     | str  | FK → `dim_vehicle.vehicle_key`.                                        |
| `date_key`        | str  | FK → `dim_date.date_key`.                                              |
| `volume_forecast` | int  | Predicted monthly volume, rounded to the nearest integer.              |
| `model_version`   | int  | The MLflow registry version that produced this row.                    |
| `model_uri`       | str  | Always `models:/ForecastTrafficVolume@production`.                     |

## How `fact_forecast_monthly.csv` was produced

1. The Day 2 training and registration pipelines were run end-to-end so that `models:/ForecastTrafficVolume@production` resolves.
2. `ml/score.py` resolved that alias via `MlflowClient` and captured its version + URI.
3. `ml/features.build_features()` was sliced to `month_start ∈ [2019-07, 2019-12]` — the holdout window from the Day 2 model card.
4. `model.predict(features[FEATURE_COLS])` produced the `volume_forecast` column.
5. Predictions were joined back to `gold.dim_plaza`, `gold.dim_vehicle`, and `gold.dim_date` to attach the surrogate keys used in the Gold layer.
6. Every row was tagged with the `@production` version that produced it.

No recursive forecasting was used: every holdout month's `lag_1` and `lag_12` are real Gold values, so the predictions in this CSV match what `make forecast` would print row-by-row.

## How to regenerate (advanced)

If you want to refresh `fact_forecast_monthly.csv` against a newer `@production` version:

```bash
make up
make build
docker compose run --rm --entrypoint python --workdir /opt ml-runner -m ml.score
```

`ml/score.py` will overwrite `fact_forecast_monthly.csv` in place.

The four `gold.*` CSVs (`dim_plaza`, `dim_vehicle`, `dim_date`, `fact_traffic_monthly`) are exported with a small `pandas.read_sql` script using the same `build_engine()` from `ml/features.py`. To regenerate them, see the `feat(day-3): commit Gold-as-CSV exports` commit message and replay the equivalent SELECTs.
