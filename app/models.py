from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(32), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    gender = Column(String(16), nullable=False, default="secret")
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    profile = relationship("Profile", back_populates="user", uselist=False)


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    avatar = Column(String(32), default="🐬")
    city = Column(String(64), default="")
    email = Column(String(128), default="")
    oicq = Column(String(32), default="")
    sig = Column(String(256), default="")
    age = Column(String(16), default="")

    user = relationship("User", back_populates="profile")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(128), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_active = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    color = Column(String(16), default="#00ff00")
    style = Column(String(16), default="normal")
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_action = Column(Boolean, default=False)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    target_user = relationship("User", foreign_keys=[target_user_id])


class GuestbookPost(Base):
    __tablename__ = "guestbook_posts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mood = Column(String(16), default="😊")
    subject = Column(String(128), default="")
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")
    replies = relationship("GuestbookReply", back_populates="post", cascade="all, delete-orphan")


class GuestbookReply(Base):
    __tablename__ = "guestbook_replies"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("guestbook_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    post = relationship("GuestbookPost", back_populates="replies")
    user = relationship("User")


class UserRoom(Base):
    __tablename__ = "user_rooms"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    room = Column(String(64), nullable=False, default="综合大厅")
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", name="uq_user_room"),)
