from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class UserPublic(BaseModel):
    id: int
    username: str
    gender: str
    is_admin: bool = False


class UserRegister(BaseModel):
    username: str = Field(min_length=2, max_length=20)
    password: str = Field(min_length=4, max_length=64)
    gender: str = "secret"


class UserLogin(BaseModel):
    username: str
    password: str


class MeResponse(BaseModel):
    user: Optional[UserPublic] = None


class ProfileUpdate(BaseModel):
    avatar: str = ""
    city: str = ""
    email: str = ""
    oicq: str = ""
    sig: str = ""
    age: str = ""
    gender: str = ""
    username: str = ""


class ProfileResponse(BaseModel):
    user: UserPublic
    avatar: str
    city: str
    email: str
    oicq: str
    sig: str
    age: str


class ChatMessageIn(BaseModel):
    content: str
    color: str = "#00ff00"
    style: str = "normal"
    target_user_id: Optional[int] = None
    is_action: bool = False


class ChatMessageOut(BaseModel):
    id: int
    user: UserPublic
    content: str
    color: str
    style: str
    target_user_id: Optional[int]
    is_action: bool
    is_system: bool
    created_at: datetime


class OnlineUser(BaseModel):
    id: int
    username: str
    gender: str
    is_admin: bool = False


class GuestbookPostIn(BaseModel):
    mood: str = "😊"
    subject: str = ""
    content: str


class GuestbookReplyIn(BaseModel):
    content: str


class GuestbookReplyOut(BaseModel):
    id: int
    user: UserPublic
    content: str
    created_at: datetime


class GuestbookPostOut(BaseModel):
    id: int
    user: UserPublic
    mood: str
    subject: str
    content: str
    created_at: datetime
    replies: List[GuestbookReplyOut]
