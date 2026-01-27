# Lender Matching Platform

A platform for matching loan applications with lender policies.

## Tech Stack

### Backend
- Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic, Hatchet

### Frontend
- React 18, TypeScript, Vite, Tailwind CSS, React Router

### Infrastructure
- PostgreSQL, Docker, GitHub Actions

## Getting Started

### Using Docker Compose

```bash
docker-compose up -d
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Manual Setup

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── core/         # Configuration and database
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── repositories/ # Data access layer
│   │   ├── services/     # Business logic
│   │   ├── rules/        # Rule engine
│   │   └── workflows/    # Hatchet workflows
│   ├── tests/
│   └── alembic/
├── frontend/
│   └── src/
│       ├── api/
│       ├── components/
│       ├── hooks/
│       ├── pages/
│       └── types/
└── docker-compose.yml
```

## Running Tests

```bash
# Backend
cd backend && pytest -v

# Frontend
cd frontend && npm test
```

## License

MIT
