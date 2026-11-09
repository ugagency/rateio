# Build a partir da raiz do repositorio:  docker build -t mut-api .
# O codigo fica em /srv/mut/backend para que Path(__file__).parents[3] (usado em avap.py)
# aponte para /srv/mut, onde estao demo_fenauto/ e dados_simulados.json.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    RATEIO_JSON_PATH=/srv/mut/dados_simulados.json \
    MUT_LEADS_DIR=/data/leads

WORKDIR /srv/mut/backend

COPY backend/pyproject.toml ./
RUN pip install --upgrade pip && pip install -e .

COPY backend/app ./app
COPY demo_fenauto /srv/mut/demo_fenauto
COPY dados_simulados.json /srv/mut/dados_simulados.json

RUN mkdir -p /data/leads
VOLUME ["/data/leads"]

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
