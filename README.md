# Regulatory Obligation Graph (ROG)

Production-grade compliance infrastructure (modular monolith) that converts regulatory documents into structured obligations, builds dependency graphs, tracks compliance, and detects regulatory changes.

## Local run (Docker)

1. Create `.env` from `.env.example` and set values.
2. Start services:

```bash
docker compose up --build
```

API will be available at `http://localhost:8000`.

Health check: `GET /health`

## Migrations (Alembic)

With `.env` set and Postgres running:

```bash
alembic upgrade head
```
