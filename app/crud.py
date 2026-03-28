from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import Session

from . import models
from .security import hash_password, verify_password, new_token, session_expiry


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.execute(select(models.User).where(models.User.username == username)).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    return db.execute(select(models.User).where(models.User.id == user_id)).scalar_one_or_none()


def create_user(db: Session, username: str, password: str, gender: str) -> models.User:
    count = db.execute(select(func.count()).select_from(models.User)).scalar_one()
    user = models.User(
        username=username,
        password_hash=hash_password(password),
        gender=gender,
        is_admin=(count == 0),
    )
    db.add(user)
    db.flush()
    profile = models.Profile(user_id=user.id)
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_session(db: Session, user_id: int) -> models.Session:
    token = new_token()
    sess = models.Session(
        user_id=user_id,
        token=token,
        expires_at=session_expiry(),
        last_active=datetime.utcnow(),
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess


def get_session(db: Session, token: str) -> Optional[models.Session]:
    if not token:
        return None
    return db.execute(select(models.Session).where(models.Session.token == token)).scalar_one_or_none()


def touch_session(db: Session, sess: models.Session) -> None:
    sess.last_active = datetime.utcnow()
    db.add(sess)
    db.commit()


def delete_session(db: Session, token: str) -> None:
    db.execute(delete(models.Session).where(models.Session.token == token))
    db.commit()


def online_users(db: Session, minutes: int = 10) -> List[models.User]:
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    sessions = db.execute(
        select(models.Session).where(models.Session.last_active >= cutoff)
    ).scalars().all()
    user_ids = {s.user_id for s in sessions}
    if not user_ids:
        return []
    return db.execute(select(models.User).where(models.User.id.in_(user_ids))).scalars().all()


def save_chat_message(
    db: Session,
    user_id: int,
    content: str,
    color: str,
    style: str,
    target_user_id: Optional[int],
    is_action: bool,
    is_system: bool = False,
) -> models.ChatMessage:
    msg = models.ChatMessage(
        user_id=user_id,
        content=content,
        color=color,
        style=style,
        target_user_id=target_user_id,
        is_action=is_action,
        is_system=is_system,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def list_chat_messages(db: Session, limit: int = 50) -> List[models.ChatMessage]:
    return (
        db.execute(
            select(models.ChatMessage).order_by(models.ChatMessage.created_at.desc()).limit(limit)
        )
        .scalars()
        .all()[::-1]
    )


def update_profile(db: Session, user: models.User, data: dict) -> models.Profile:
    profile = user.profile
    if not profile:
        profile = models.Profile(user_id=user.id)
        db.add(profile)
        db.flush()
    for key in ["avatar", "city", "email", "oicq", "sig", "age"]:
        if key in data and data[key] is not None:
            setattr(profile, key, data[key])
    if "gender" in data and data["gender"]:
        user.gender = data["gender"]
    if "username" in data and data["username"]:
        existing = get_user_by_username(db, data["username"])
        if existing and existing.id != user.id:
            raise ValueError("Username exists")
        user.username = data["username"]
    db.add(user)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def set_user_room(db: Session, user_id: int, room: str) -> None:
    existing = db.execute(select(models.UserRoom).where(models.UserRoom.user_id == user_id)).scalar_one_or_none()
    if existing:
        existing.room = room
        existing.updated_at = datetime.utcnow()
        db.add(existing)
    else:
        db.add(models.UserRoom(user_id=user_id, room=room))
    db.commit()


def get_user_room(db: Session, user_id: int) -> str:
    existing = db.execute(select(models.UserRoom).where(models.UserRoom.user_id == user_id)).scalar_one_or_none()
    return existing.room if existing else "综合大厅"


def create_post(db: Session, user_id: int, mood: str, subject: str, content: str) -> models.GuestbookPost:
    post = models.GuestbookPost(user_id=user_id, mood=mood, subject=subject, content=content)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def list_posts(db: Session) -> List[models.GuestbookPost]:
    return db.execute(select(models.GuestbookPost).order_by(models.GuestbookPost.created_at.desc())).scalars().all()


def create_reply(db: Session, post_id: int, user_id: int, content: str) -> models.GuestbookReply:
    reply = models.GuestbookReply(post_id=post_id, user_id=user_id, content=content)
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply


def delete_post(db: Session, post_id: int, user_id: int, is_admin: bool) -> bool:
    post = db.execute(select(models.GuestbookPost).where(models.GuestbookPost.id == post_id)).scalar_one_or_none()
    if not post:
        return False
    if post.user_id != user_id and not is_admin:
        return False
    db.delete(post)
    db.commit()
    return True


def delete_reply(db: Session, reply_id: int, user_id: int, is_admin: bool) -> bool:
    reply = db.execute(select(models.GuestbookReply).where(models.GuestbookReply.id == reply_id)).scalar_one_or_none()
    if not reply:
        return False
    if reply.user_id != user_id and not is_admin:
        return False
    db.delete(reply)
    db.commit()
    return True
