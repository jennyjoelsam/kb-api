"""Tests that data really survives: written by one connection, read by a new one."""
import time

from sqlalchemy.orm import sessionmaker

from app import crud
from app.database import Base, make_engine
from app.schemas import Document, DocumentCreate


def test_data_persists_across_new_connections(tmp_path):
    url = f"sqlite:///{tmp_path / 'test.db'}"

    first_engine = make_engine(url)
    Base.metadata.create_all(first_engine)
    with sessionmaker(bind=first_engine)() as db:
        crud.create(db, DocumentCreate(title="Persistent", content="Still here", tags=["a"]))
    first_engine.dispose()  # simulates the server shutting down

    second_engine = make_engine(url)  # simulates a fresh start
    with sessionmaker(bind=second_engine)() as db:
        docs = crud.all_documents(db)
    assert [d.title for d in docs] == ["Persistent"]
    assert docs[0].tags == ["a"]
    second_engine.dispose()


def test_timestamps_come_back_labelled_as_utc(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'ts.db'}")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as db:
        row = crud.create(db, DocumentCreate(title="T", content="C"))
        db.expire_all()  # force a re-read from the database
        doc = Document.model_validate(crud.get(db, row.id))
    assert doc.created_at.tzinfo is not None
    assert doc.created_at.utcoffset().total_seconds() == 0
    engine.dispose()


def test_update_changes_updated_at_but_not_created_at(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'upd.db'}")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as db:
        row = crud.create(db, DocumentCreate(title="Old", content="C"))
        created = row.created_at
        time.sleep(0.01)  # make sure the clock moves so the difference is visible
        updated = crud.update(db, row.id, DocumentCreate(title="New", content="C2"))
        assert updated.title == "New"
        assert updated.created_at == created
        assert updated.updated_at > created
    engine.dispose()
