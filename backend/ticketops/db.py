from datetime import datetime, timezone
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import settings

def utcnow():
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    pass

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False, "timeout": 30} if settings.database_url.startswith("sqlite") else {}, pool_pre_ping=True)
if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def sqlite_config(conn, _):
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")

Session = sessionmaker(bind=engine, expire_on_commit=False)

def get_db():
    with Session() as db:
        yield db
