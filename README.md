# Knowledge Base API

A REST API built with FastAPI and SQLite for storing, managing and searching text documents (FAQs, policies, guides). It is the foundation for a later Retrieval-Augmented Generation (RAG) support assistant.

**Status:** version 0.2. Persistent storage, tests, Docker and CI included.

## Features
- Create, read, update, delete documents (title, content, tags), stored in SQLite
- Input validation with Pydantic (clear `422` errors for bad input, `404` for missing documents)
- Tag filtering and pagination on the document list
- Keyword search with ranking: title matches count 3x, tag matches 2x, body matches 1x
- Health check that also verifies the database connection
- Request logging (method, path, status, duration)
- Settings through environment variables (`DATABASE_URL`, `LOG_LEVEL`)
- 32 automated tests (pytest), run on every push by GitHub Actions
- Dockerfile for deployment
- Auto-generated interactive docs at `/docs`

## Run it locally
Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+.

```bash
uv sync
uv run fastapi dev
```

Open http://127.0.0.1:8000/docs to try every endpoint in the browser. Data is saved in `kb.db` in the project folder.

## Run with Docker
```bash
docker build -t kb-api .
docker run -p 8000:8000 -v kb-data:/data kb-api
```
The named volume `kb-data` keeps the database between container restarts.

## Endpoints
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Service is alive and the database is reachable |
| POST | `/documents` | Create a document (201) |
| GET | `/documents?tag=&skip=&limit=` | List, filter by tag, paginate |
| GET | `/documents/{id}` | Get one (404 if missing) |
| PUT | `/documents/{id}` | Replace one (404 if missing) |
| DELETE | `/documents/{id}` | Delete one (204; 404 if missing) |
| GET | `/search?q=&limit=` | Ranked keyword search |

Example:
```bash
curl -X POST http://127.0.0.1:8000/documents \
  -H 'Content-Type: application/json' \
  -d '{"title":"Refund policy","content":"Refunds within 30 days.","tags":["billing"]}'

curl "http://127.0.0.1:8000/search?q=refund"
```

## Run the tests
```bash
uv run pytest
```
Tests use a throwaway in-memory database, so they never touch `kb.db`.

## Project layout
```
app/
  main.py       endpoints, startup, request logging (web layer)
  schemas.py    Pydantic models: request/response shapes and validation
  models.py     SQLAlchemy table definition (database layer)
  database.py   engine, sessions, per-request session dependency
  crud.py       create/read/update/delete queries
  search.py     tokenizing and scoring
  config.py     environment-variable settings
tests/          pytest suites: endpoints, search, persistence
Dockerfile      container image
.github/workflows/tests.yml   CI: run tests on every push
```
Each layer has one job: endpoints do not write SQL, and database code knows nothing about HTTP.

## Configuration
| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./kb.db` | Database location |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Known limitations
- Search matches whole words exactly: "refund" does not match "refunds" (no stemming).
- Search loads all documents into memory to score them; fine for thousands of documents, not millions.
- No authentication or rate limiting.
- SQLite suits a single server; a larger deployment would move to PostgreSQL.
- No database migrations yet (schema changes require a new database file).

## Roadmap
1. BM25 ranking and semantic (embedding) search
2. RAG answers with source citations, plus an evaluation set (the Support Copilot project)
3. Authentication and migrations
