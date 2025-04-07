# backend/db.py

from sqlmodel import SQLModel, create_engine, Session as DBSession
from .models import Session

sqlite_file = "traeger.db"
engine = create_engine(f"sqlite:///{sqlite_file}", echo=False)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_db():
    with DBSession(engine) as session:
        yield session
