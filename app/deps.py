from __future__ import annotations

from datetime import datetime

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .db import SessionLocal
from . import crud
from .config import app_settings


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    session: str | None = Cookie(default=None, alias=app_settings.session_cookie_name),
    db: Session = Depends(get_db),
):
    if not session:
        return None
    sess = crud.get_session(db, session)
    if not sess:
        return None
    if sess.expires_at <= datetime.utcnow():
        return None
    crud.touch_session(db, sess)
    return sess.user


def require_user(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")
    return user
