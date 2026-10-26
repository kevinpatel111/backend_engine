# Backend Engine — Production-Ready REST API

[![CI Pipeline](https://github.com/kevinpatel111/backend_engine/actions/workflows/ci.yml/badge.svg)](https://github.com/kevinpatel111/backend_engine/actions)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791.svg?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue.svg)](http://mypy-lang.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A production-grade, asynchronous REST API built with **FastAPI**, **SQLAlchemy 2.0 (Async)**, **PostgreSQL**, and **Pydantic v2**. Designed following strict separation of concerns (Routes ➔ Services ➔ Repositories), enterprise authentication with Argon2 and rotating JWTs, RBAC authorization, and containerized deployment workflows.

---

## 🌟 Key Features

- **Layered Architecture**: Strict boundaries between HTTP handlers (Routes), business rules (Services), and database persistence (Repositories).
- **Asynchronous Stack**: Built on `asyncpg` and SQLAlchemy 2.0 async sessions with automatic connection pooling and failure rollback.
- **Enterprise Authentication & Security**:
  - Secure password hashing using **Argon2** via `pwdlib`.
  - Short-lived JWT access tokens and long-lived **rotating refresh tokens**.
  - Database-backed refresh token revocation tracking and instant logout invalidation.
  - Role-Based Access Control (**RBAC**) supporting `user` and `admin` roles.
  - Resource ownership validation preventing cross-tenant data tampering.
- **Alembic Database Migrations**: Version-controlled asynchronous schema evolution.
- **Pydantic v2 Validation**: Strong schema boundaries separating input payloads, updates, and serialized response representations with mass-assignment protection.
- **Reusable Pagination, Filtering & Sorting**: Declarative page, limit, search, and sort validation across endpoints.
- **Automated Testing Suite**: Full suite of unit and integration tests using `pytest`, `pytest-asyncio`, and `httpx.AsyncClient` against isolated in-memory test databases.
- **Code Quality & CI/CD**: Zero-warning `ruff` linting and formatting, `mypy` strict static typing, and automated GitHub Actions pipeline.
- **Containerization**: Production multi-stage Dockerfile and Docker Compose orchestration with PostgreSQL health checks.

---

## 🏛️ Application Architecture

```
Client (HTTP Request)
        │
        ▼
[ API Routes Layer ] (app/api/v1/)
  - Route definitions & status codes
  - Dependency injection (CurrentUser, DB Session)
  - Pydantic validation & response serialization
        │
        ▼
[ Services Layer ] (app/services/)
  - Business logic orchestration
  - Ownership & permission enforcement
  - Transaction boundaries & AppException handling
        │
        ▼
[ Repositories Layer ] (app/repositories/)
  - Database persistence & queries
  - SQLAlchemy 2.0 async queries & filtering
        │
        ▼
[ PostgreSQL / Database ]
```

---

## 📂 Project Structure

```
backend-engine/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app, lifespan, CORS, error handlers
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py           # v1 aggregator router
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── auth.py         # /register, /login, /refresh, /logout
│   │           ├── users.py        # /me, /{user_id}, admin user management
│   │           └── products.py     # Product CRUD, pagination, filtering
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Pydantic Settings configuration
│   │   ├── security.py             # Argon2 password hash & JWT encode/decode
│   │   ├── exceptions.py           # Domain exceptions (NotFound, Forbidden, etc.)
│   │   └── logging.py              # Structured application logger
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py                 # DeclarativeBase & TimestampMixin
│   │   └── session.py              # Async engine & session dependency
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                 # User and RefreshToken models
│   │   └── product.py              # Product model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py                 # Token, Login, Refresh schemas
│   │   ├── user.py                 # UserCreate, UserUpdate, UserResponse
│   │   └── product.py              # ProductCreate, ProductUpdate, ProductResponse
│   ├── services/
│   │   ├── __init__.py
│   │   ├── authservice.py          # Registration, login, token rotation logic
│   │   ├── userservice.py          # Profile, role changes, authorization
│   │   └── productservice.py       # Product business logic & ownership
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── userrepository.py       # User & token SQL persistence
│   │   └── productrepository.py    # Product queries, sorting, pagination
│   ├── dependencies/
│   │   ├── __init__.py
│   │   ├── auth.py                 # OAuth2 bearer & get_current_user
│   │   └── permissions.py          # RoleChecker (require_admin, etc.)
│   └── utils/
│       ├── __init__.py
│       └── pagination.py           # PaginatedResponse generic schema
├── alembic/
│   ├── env.py                      # Async migration runner
│   ├── script.py.mako              # Revision template
│   └── versions/                   # Migration versions
├── tests/
│   ├── conftest.py                 # Pytest fixtures & isolated DB
│   ├── unit/
│   │   ├── test_auth_service.py    # AuthService unit tests
│   │   └── test_product_service.py # ProductService unit tests
│   └── integration/
│       ├── test_auth.py            # Auth endpoint flow tests
│       ├── test_users.py           # User endpoint & RBAC tests
│       └── test_products.py        # Product CRUD & scoping tests
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions CI workflow
├── .env.example                    # Environment template
├── .gitignore
├── Dockerfile                      # Production multi-stage Docker build
├── docker-compose.yml              # Local PostgreSQL + API orchestration
├── alembic.ini                     # Migration configuration
├── pyproject.toml                  # Project metadata & tool config
├── requirements.txt                # Locked application dependencies
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **PostgreSQL 14+** (or Docker for containerized setup)
- `uv` (recommended) or standard `pip`

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/example/backend-engine.git
cd backend-engine

# Copy configuration
cp .env.example .env

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install greenlet
```

### 2. Configure Environment Variables (`.env`)

Edit `.env` with your secure credentials:

```ini
ENVIRONMENT=development
DEBUG=True
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/backend_engine_db
JWT_SECRET_KEY=generate-a-strong-32-character-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
LOG_LEVEL=INFO
```

### 3. Run Database Migrations

Apply database migrations using Alembic:

```bash
alembic upgrade head
```

### 4. Start the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access the interactive API documentation at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Schema**: [http://localhost:8000/api/v1/openapi.json](http://localhost:8000/api/v1/openapi.json)

---

## 🐳 Docker Deployment

To spin up the entire stack (FastAPI + PostgreSQL) with a single command:

```bash
# Build and run containers in detached mode
docker compose up -d --build

# Run database migrations inside container
docker compose exec api alembic upgrade head

# Inspect application logs
docker compose logs -f api

# Stop containers and keep data volumes
docker compose down
```

---

## 🧪 Testing & Code Quality

### Running Tests

Execute the complete automated test suite:

```bash
pytest -v
```

### Linting & Formatting

```bash
# Run Ruff lint check
ruff check .

# Run Ruff formatting check
ruff format --check .

# Automatically apply Ruff fixes
ruff check . --fix
```

### Static Type Checking

```bash
mypy app
```

---

## 📚 API Reference

All application endpoints are prefixed with `/api/v1`.

### 🔐 Authentication

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Register a new user | No |
| `POST` | `/api/v1/auth/login` | Authenticate and obtain JWT access & refresh tokens | No |
| `POST` | `/api/v1/auth/refresh` | Rotate tokens using a valid refresh token | No |
| `POST` | `/api/v1/auth/logout` | Revoke a refresh token and end session | No |

### 👤 Users

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/users/me` | Retrieve profile of authenticated user | Bearer Token |
| `PATCH` | `/api/v1/users/me` | Update profile of authenticated user | Bearer Token |
| `GET` | `/api/v1/users/` | List and search all users (Paginated) | **Admin only** |
| `GET` | `/api/v1/users/{user_id}` | Retrieve specific user profile | Owner or Admin |
| `PATCH` | `/api/v1/users/{user_id}` | Update user fields (Roles restricted to admin) | Owner or Admin |
| `DELETE` | `/api/v1/users/{user_id}` | Delete user account | Owner or Admin |

### 📦 Products

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/products/` | Create a new product owned by caller | Bearer Token |
| `GET` | `/api/v1/products/` | List products with pagination, search, sorting | Bearer Token |
| `GET` | `/api/v1/products/{product_id}` | Retrieve product details | Owner or Admin |
| `PATCH` | `/api/v1/products/{product_id}` | Update product attributes | Owner or Admin |
| `DELETE` | `/api/v1/products/{product_id}` | Delete product | Owner or Admin |

---

## 📡 Example API Requests

### 1. Register a User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "developer@example.com",
    "full_name": "Jane Developer",
    "password": "StrongPassword123!"
  }'
```

### 2. Login & Obtain Tokens

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "developer@example.com",
    "password": "StrongPassword123!"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

### 3. Create a Product

```bash
curl -X POST "http://localhost:8000/api/v1/products/" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cloud Storage Subscription",
    "description": "1TB secure NVMe cloud storage tier",
    "price": 9.99
  }'
```

### 4. Search and Paginate Products

```bash
curl -X GET "http://localhost:8000/api/v1/products/?page=1&page_size=10&search=Cloud&sort_by=price&sort_order=desc" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Response:**
```json
{
  "items": [
    {
      "id": "c1f7b090-0c42-4f18-bb5c-755e1db45719",
      "name": "Cloud Storage Subscription",
      "description": "1TB secure NVMe cloud storage tier",
      "price": 9.99,
      "owner_id": "89ecb0be-aa48-4389-98e6-121f64f33d01",
      "created_at": "2026-10-14T10:45:00Z",
      "updated_at": "2026-10-14T10:45:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

---

## ☁️ Production Deployment Guide

### Deploying to Render / Railway / AWS ECS

1. **Managed Database Provisioning**:
   - Provision a managed PostgreSQL instance (e.g., AWS RDS, Supabase, Neon, or Render PostgreSQL).
   - Set the `DATABASE_URL` environment variable:
     ```
     DATABASE_URL=postgresql+asyncpg://<db_user>:<db_password>@<db_host>:5432/<db_name>
     ```
2. **Secrets Configuration**:
   - Generate a cryptographically secure 256-bit secret key:
     ```bash
     python -c "import secrets; print(secrets.token_hex(32))"
     ```
   - Store `JWT_SECRET_KEY` in your hosting platform's secret manager.
3. **Database Migrations as Release Step**:
   - Configure a release phase command to execute before traffic routing:
     ```bash
     alembic upgrade head
     ```
4. **Process Execution**:
   - For high-concurrency production deployments, execute with Uvicorn worker clustering:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers --forwarded-allow-ips='*'
     ```
5. **CORS & SSL**:
   - Set `BACKEND_CORS_ORIGINS=["https://yourdomain.com"]` to deny untrusted origins.
   - Enforce HTTPS termination at the load balancer / reverse proxy layer.

---

## 🔮 Future Improvements

- Add Redis-based distributed caching and token revocation blacklists.
- Implement rate limiting with slowapi / token-bucket algorithms.
- Integrate Celery or ARQ for asynchronous background tasks and transactional email dispatch.
- Add Prometheus `/metrics` endpoint with OpenTelemetry distributed tracing.

---

## 📄 License

This project is open-sourced under the MIT License.
