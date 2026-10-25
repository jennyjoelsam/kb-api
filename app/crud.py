"""Database operations (Create, Read, Update, Delete).

Every function receives a `db` session. No web code here, so it can be tested
without starting a server.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DocumentRow, utcnow
from app.schemas import DocumentCreate


def create(db: Session, data: DocumentCreate) -> DocumentRow:
    row = DocumentRow(**data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get(db: Session, doc_id: int) -> DocumentRow | None:
    return db.get(DocumentRow, doc_id)


def list_documents(db: Session, tag: str | None = None, skip: int = 0, limit: int = 20) -> list[DocumentRow]:
    query = select(DocumentRow).order_by(DocumentRow.id)
    if tag is None:
        return list(db.scalars(query.offset(skip).limit(limit)))
    # Tags live in a JSON column, so filter them in Python, then paginate.
    wanted = tag.lower()
    matching = [r for r in db.scalars(query) if wanted in (t.lower() for t in r.tags)]
    return matching[skip : skip + limit]


def update(db: Session, doc_id: int, data: DocumentCreate) -> DocumentRow | None:
    row = db.get(DocumentRow, doc_id)
    if row is None:
        return None
    row.title, row.content, row.tags = data.title, data.content, data.tags
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete(db: Session, doc_id: int) -> bool:
    row = db.get(DocumentRow, doc_id)
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True


def all_documents(db: Session) -> list[DocumentRow]:
    return list(db.scalars(select(DocumentRow).order_by(DocumentRow.id)))
