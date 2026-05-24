"""MEMBRA CompanyOS — SQLAlchemy declarative base and engine."""
import uuid
from sqlalchemy import create_engine, event, TypeDecorator, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import QueuePool, NullPool

from app.core.config import get_settings

settings = get_settings()

_url = str(settings.DATABASE_URL)
_is_sqlite = _url.startswith("sqlite")


class GUID(TypeDecorator):
    """Platform-independent GUID type. Uses String(36) for SQLite, native UUID for PostgreSQL."""
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID
            return dialect.type_descriptor(UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(str(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(str(value))
        return value


if _is_sqlite:
    engine = create_engine(
        _url,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
        echo=settings.DEBUG,
    )
else:
    engine = create_engine(
        _url,
        poolclass=QueuePool,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
