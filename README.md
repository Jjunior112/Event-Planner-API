# Event Planner API

Plataforma SaaS de gestão de eventos (casamentos) com arquitetura multi-tenant.

## Stack

- **FastAPI** — API REST assíncrona
- **SQLAlchemy 2.0** — ORM async com PostgreSQL
- **Alembic** — Migrações de banco de dados
- **Docker Compose** — Ambiente de desenvolvimento

## Estrutura do Projeto

```
app/
├── core/           # Configuração, database, dependências globais
├── models/         # Entidades SQLAlchemy
├── schemas/        # DTOs Pydantic (request/response)
├── services/       # Regras de negócio
├── repositories/   # Acesso a dados
├── routers/        # Endpoints FastAPI
└── main.py         # Ponto de entrada da aplicação
```

## Pré-requisitos

- Python 3.12+
- Docker e Docker Compose

## Setup Local

### 1. Clonar e configurar ambiente

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Subir infraestrutura com Docker

```bash
docker compose up -d db
```

### 3. Rodar migrações

```bash
alembic upgrade head
```

### 4. Iniciar a API

```bash
# Local
uvicorn app.main:app --reload

# Ou via Docker (API + DB)
docker compose up
```

A API estará disponível em `http://localhost:8000`.

- **Docs (Swagger):** `http://localhost:8000/docs`
- **Health check:** `http://localhost:8000/health`

## Roadmap (Milestones)

| # | Milestone | Status |
|---|-----------|--------|
| M1 | Infraestrutura (FastAPI, Docker, SQLAlchemy, Alembic) | ✅ |
| M2 | Auth (User, JWT) | ✅ |
| M3 | Workspaces (multi-tenancy) | ✅ |
| M4 | Events | ✅ |
| M5 | Categories | ✅ |
| M6 | Suppliers | ✅ |
| M7 | Quotes | ✅ |
| M8 | Dashboard | ✅ |
| M9 | Checklist | ✅ |
| M10 | Calendar | ✅ |
| M11 | Payments | ✅ |
| M12 | Contracts | ✅ |
| M13 | Audit Log | ✅ |
| M14 | Notifications | ✅ |

## Frontend (M15+)

O front-end React está em `frontend/`. Veja [frontend/README.md](frontend/README.md).

| # | Milestone | Status |
|---|-----------|--------|
| M15 | React Base (auth, dashboard, rotas) | ✅ |
| M16 | Gráficos financeiros | ✅ |
| M17 | Gestão de membros/permissões | ✅ |
| M18 | Stripe / Mercado Pago webhooks | ✅ |
| M19 | Planos (Free, Starter, Premium) | ✅ |
| M20 | Limites por plano | ✅ |
| M21 | Admin Panel | ✅ |

## Convenções

- Toda entidade herda de `TimestampMixin` (`id`, `created_at`, `updated_at`, `deleted_at`)
- Soft delete via campo `deleted_at`
- Isolamento por `Workspace` em todas as rotas de domínio
- Clean Architecture: Models → Repositories → Services → Routers
