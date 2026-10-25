import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    """A fake browser calling our API, backed by a throwaway in-memory database.

    Every test gets a brand-new empty database, so tests cannot affect each other
    and your real kb.db file is never touched.
    """
    # StaticPool: an in-memory SQLite database lives on one connection, so share it.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    # Tell FastAPI: wherever an endpoint asks for get_db, use the test database instead.
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def make_doc(client: TestClient):
    """Helper: create a document through the API and return its JSON."""

    def _make(title="Reset password", content="Click forgot password on the login page.", tags=None):
        body = {"title": title, "content": content, "tags": tags or []}
        response = client.post("/documents", json=body)
        assert response.status_code == 201
        return response.json()

    return _make
