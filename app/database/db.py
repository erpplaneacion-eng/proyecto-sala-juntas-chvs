import os
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from ..config import load_environment

load_environment()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

# Railway may provide postgres://, SQLAlchemy expects postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


def _sanitize_postgres_url(url: str) -> str:
    """Percent-encode user/password to avoid DSN parsing issues with special chars."""
    parsed = urlsplit(url)
    if not parsed.scheme.startswith("postgresql"):
        return url
    if "@" not in parsed.netloc:
        return url

    userinfo, hostinfo = parsed.netloc.rsplit("@", 1)
    has_password = ":" in userinfo
    username, password = userinfo.split(":", 1) if has_password else (userinfo, "")

    safe_username = quote(unquote(username), safe="")
    safe_password = quote(unquote(password), safe="")
    safe_userinfo = f"{safe_username}:{safe_password}" if has_password else safe_username
    safe_netloc = f"{safe_userinfo}@{hostinfo}"
    return urlunsplit((parsed.scheme, safe_netloc, parsed.path, parsed.query, parsed.fragment))


DATABASE_URL = _sanitize_postgres_url(DATABASE_URL)

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
