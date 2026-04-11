from __future__ import annotations

import os


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    database_url = os.getenv("DATABASE_URL", "sqlite:///./red_dragonfly.db")
    session_cookie_name = os.getenv("SESSION_COOKIE_NAME", "session")
    session_cookie_secure = _get_bool("SESSION_COOKIE_SECURE", False)
    session_cookie_samesite = os.getenv("SESSION_COOKIE_SAMESITE", "lax")
    session_cookie_domain = os.getenv("SESSION_COOKIE_DOMAIN") or None

    @property
    def normalized_database_url(self) -> str:
        # Accept postgres:// in env files for compatibility with common hosting defaults.
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+psycopg://", 1)
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return self.database_url


app_settings = Settings()
