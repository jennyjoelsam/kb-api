"""Knowledge Base API: the web layer.

Each function below is an *endpoint*: a URL + HTTP method that runs Python code.
"""
import logging
import time
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app import crud, models  # noqa: F401  (importing models registers the tables)
from app.config import LOG_LEVEL
from app.database import Base, engine, get_db
from app.schemas import Document, DocumentCreate, SearchResult
from app.search import search

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("kb_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once at startup: create the tables if they do not exist yet."""
    Base.metadata.create_all(engine)
    logger.info("Database ready")
    yield


app = FastAPI(
    title="Knowledge Base API",
    description="Store, manage and keyword-search documents.",
    version="0.2.0",
    lifespan=lifespan,
)

# A type shortcut: any endpoint parameter of this type receives a database session.
DbSession = Annotated[Session, Depends(get_db)]


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every request: method, path, status code and how long it took."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("%s %s -> %s (%.1f ms)", request.method, request.url.path, response.status_code, elapsed_ms)
    return response


@app.get("/health")
def health(db: DbSession) -> dict[str, str]:
    """Is the service alive and can it reach the database?"""
    db.connection()  # raises if the database is unreachable
    return {"status": "ok"}


@app.post("/documents", response_model=Document, status_code=status.HTTP_201_CREATED)
def create_document(data: DocumentCreate, db: DbSession):
    """Create a document. FastAPI reads the JSON body and validates it against DocumentCreate."""
    row = crud.create(db, data)
    logger.info("Created document %s", row.id)
    return row


@app.get("/documents", response_model=list[Document])
def list_documents(
    db: DbSession,
    tag: str | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List documents, optionally filtered by tag. skip/limit give simple pagination."""
    return crud.list_documents(db, tag=tag, skip=skip, limit=limit)


@app.get("/documents/{doc_id}", response_model=Document)
def get_document(doc_id: int, db: DbSession):
    row = crud.get(db, doc_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    return row


@app.put("/documents/{doc_id}", response_model=Document)
def replace_document(doc_id: int, data: DocumentCreate, db: DbSession):
    row = crud.update(db, doc_id, data)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    return row


@app.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(doc_id: int, db: DbSession) -> Response:
    if not crud.delete(db, doc_id):
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    logger.info("Deleted document %s", doc_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/search", response_model=list[SearchResult])
def search_documents(
    db: DbSession,
    q: Annotated[str, Query(min_length=1, description="Words to look for")],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
):
    """Keyword search, best matches first."""
    docs = [Document.model_validate(row) for row in crud.all_documents(db)]
    return search(q, docs, limit=limit)
