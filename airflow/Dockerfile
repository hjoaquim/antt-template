# Airflow image with dbt-postgres + ML stack baked in. Building locally
# keeps the Compose file pinned to a known-good combination and avoids
# per-container pip installs at runtime.
FROM apache/airflow:3.2.1-python3.11

# dbt-postgres pulls dbt-core as a transitive dependency. sqlalchemy and
# psycopg2-binary are already shipped with Airflow. The Day 2 additions
# (mlflow, scikit-learn, pytest) live alongside the Day 1 pins so a
# single image serves both the orchestration and the training workflows.
USER airflow
RUN pip install --no-cache-dir \
    "dbt-postgres==1.8.2" \
    "pandas==2.2.3" \
    "mlflow==2.18.0" \
    "scikit-learn==1.5.2" \
    "pytest==8.3.3"
