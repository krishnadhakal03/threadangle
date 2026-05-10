import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy import event
from dotenv import load_dotenv

load_dotenv()

def _normalize_database_url(raw_url: str) -> str:
    if not raw_url.startswith("sqlite"):
        return raw_url

    prefix, sep, db_path = raw_url.partition(":///")
    if not sep or not db_path or db_path == ":memory:":
        return raw_url

    if os.path.isabs(db_path):
        return raw_url

    base_dir = Path(__file__).resolve().parent
    absolute_path = (base_dir / db_path).resolve()
    return f"{prefix}:///{absolute_path.as_posix()}"


DATABASE_URL = _normalize_database_url(
    os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./threadangle.db")
)

_echo = (
    os.getenv("SQLALCHEMY_ECHO", "0") == "1"
    and os.getenv("ENVIRONMENT", "development").strip().lower() != "production"
)

# SQLite + async + frequent polling/background tasks can easily exhaust the default
# QueuePool (size=5, overflow=10). For local SQLite we prefer NullPool so each session
# gets a fresh connection and returns it immediately, avoiding pool timeouts.
_engine_kwargs = {"echo": _echo}
if DATABASE_URL.startswith("sqlite"):
    # SQLite locking mitigations:
    # - WAL allows one writer + concurrent readers (big win for polling + background tasks)
    # - busy_timeout makes SQLite wait for locks instead of failing instantly
    # - higher timeout gives the driver more time before raising "database is locked"
    _engine_kwargs.update(
        {
            "poolclass": NullPool,
            "connect_args": {"timeout": int(os.getenv("SQLITE_TIMEOUT_SECONDS", "60"))},
        }
    )
else:
    # For non-sqlite DBs, keep pooling but allow tuning via env.
    _engine_kwargs.update(
        {
            "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
            "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
            "pool_pre_ping": True,
        }
    )

engine = create_async_engine(DATABASE_URL, **_engine_kwargs)

if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):  # type: ignore[no-redef]
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.execute(f"PRAGMA busy_timeout={int(os.getenv('SQLITE_BUSY_TIMEOUT_MS', '10000'))};")
            cursor.close()
        except Exception:
            # Don't fail startup if PRAGMA isn't supported for some reason.
            pass

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
