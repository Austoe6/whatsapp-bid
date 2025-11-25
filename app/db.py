from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

is_sqlite = settings.database_url.startswith("sqlite")
engine_kwargs = {"future": True}

if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # In serverless environments, avoid persistent pools; rely on external pooling (e.g., Supabase pgbouncer)
    from sqlalchemy.pool import NullPool

    engine_kwargs["poolclass"] = NullPool

engine = create_engine(settings.database_url, **engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()