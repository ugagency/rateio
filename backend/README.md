# Motor de Rateio — Backend

API FastAPI para a Plataforma Mutualiza.

## Setup local

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

Docs interativas: http://localhost:8000/docs

## Modos de repositório

- `RATEIO_REPOSITORY=json` (default) — lê `dados_simulados.json` em memória; ideal para dev e testes.
- `RATEIO_REPOSITORY=supabase` — lê do Postgres do Supabase real.

## Testes

```bash
pytest -v
```

O teste golden valida o alvo R$ 716.964,00 e diff = 0 contra `dados_simulados.json`.
