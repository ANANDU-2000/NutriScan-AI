import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nutriscan.db")
# Render PostgreSQL uses postgres:// but SQLAlchemy 1.4+ needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

_connect_args = {}
if "sqlite" in DATABASE_URL:
    _connect_args = {"check_same_thread": False}
elif "postgresql" in DATABASE_URL and "sslmode" not in DATABASE_URL:
    # Render/external Postgres often requires TLS; pool_pre_ping avoids stale connections after idle
    _connect_args = {"sslmode": "require"}

engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Ensure all tables (including new ones) are created without dropping existing data
Base.metadata.create_all(bind=engine)
