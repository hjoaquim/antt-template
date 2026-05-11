# Day 2 ML image.
#
# Serves two purposes from a single build:
#   1. The `mlflow` service runs `mlflow server` (the tracking server).
#   2. The `ml-runner` service runs the Day 2 training scripts in
#      /opt/ml on demand (`make train-once`, `make sweep`, etc.).
#
# A single image keeps Day 2 dependencies in one place and the Day 1
# airflow image untouched.
FROM python:3.11-slim

RUN pip install --no-cache-dir \
    "mlflow==2.18.0" \
    "scikit-learn==1.5.2" \
    "pandas==2.2.3" \
    "psycopg2-binary==2.9.10" \
    "sqlalchemy==2.0.36" \
    "pytest==8.3.3"

EXPOSE 5000

# Default command runs the tracking server; ml-runner overrides this.
CMD ["mlflow", "server", \
     "--host", "0.0.0.0", \
     "--port", "5000", \
     "--backend-store-uri", "sqlite:////mlruns/mlflow.db", \
     "--default-artifact-root", "/mlruns/artifacts"]
