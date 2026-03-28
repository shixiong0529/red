from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from . import models
from .security import hash_password


@dataclass(frozen=True)
class BotDef:
    username: str
    gender: str
    color: str
    is_admin: bool


def _read_bak() -> str:
    return Path("bak/red-dragonfly-chatroom.html").read_text("utf-8", errors="replace")


def _extract_js_array(text: str, var_name: str) -> str:
    m = re.search(rf"var {re.escape(var_name)}=\[(.*?)\];", text, re.S)
    if not m:
        raise ValueError(f"Cannot find var {var_name}=[...]")
    return "[" + m.group(1) + "]"


def _extract_gb_msgs(text: str) -> list[dict[str, Any]]:
    m = re.search(r"var gbMsgs=\[(.*?\n)\],gbId=", text, re.S)
    if not m:
        raise ValueError("Cannot find var gbMsgs=[...]")
    blob = "[" + m.group(1) + "]"
    blob = re.sub(r"//.*", "", blob)
    blob = blob.replace("true", "True").replace("false", "False").replace("null", "None")
    blob = re.sub(r"([\{,]\s*)([a-zA-Z_]\w*)\s*:", r"\1'\2':", blob)
    return ast.literal_eval(blob)


def _extract_bot_profiles(text: str) -> list[dict[str, Any]]:
    m = re.search(r"var botProfiles=\[(.*?\n)\];", text, re.S)
    if not m:
        return []
    blob = "[" + m.group(1) + "]"
    blob = re.sub(r"//.*", "", blob)
    blob = blob.replace("true", "True").replace("false", "False").replace("null", "None")
    blob = re.sub(r"([\{,]\s*)([a-zA-Z_]\w*)\s*:", r"\1'\2':", blob)
    return ast.literal_eval(blob)


def _parse_datetime(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def _ensure_user(
    db: Session,
    username: str,
    password: str,
    gender: str,
    is_admin: bool = False,
    created_at: datetime | None = None,
) -> models.User:
    user = db.execute(select(models.User).where(models.User.username == username)).scalar_one_or_none()
    if user:
        return user
    user = models.User(
        username=username,
        password_hash=hash_password(password),
        gender=gender,
        is_admin=is_admin,
        created_at=created_at or datetime.utcnow(),
    )
    db.add(user)
    db.flush()
    profile = models.Profile(user_id=user.id)
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user


def seed_if_needed(db: Session) -> None:
    text = _read_bak()

    bots_literal = _extract_js_array(text, "bots")
    bot_msgs_literal = _extract_js_array(text, "botMsgs")
    bot_profiles = _extract_bot_profiles(text)
    gb_msgs = _extract_gb_msgs(text)

    # Parse bots / messages using Python literal_eval after quoting keys.
    bots_blob = re.sub(r"([\{,]\s*)([a-zA-Z_]\w*)\s*:", r"\1'\2':", bots_literal)
    bots_list: list[dict[str, Any]] = ast.literal_eval(bots_blob)
    bot_msgs: list[str] = ast.literal_eval(bot_msgs_literal.replace("true", "True").replace("false", "False"))

    bots: list[BotDef] = []
    for b in bots_list:
        bots.append(
            BotDef(
                username=b["n"],
                gender=b.get("g", "secret"),
                color=b.get("c", "#00ff00"),
                is_admin=bool(b.get("a")),
            )
        )

    prof_by_name: dict[str, dict[str, Any]] = {p.get("n"): p for p in bot_profiles if p.get("n")}

    # Create bot users + profiles.
    for b in bots:
        p = prof_by_name.get(b.username, {})
        created_at = None
        if p.get("reg"):
            try:
                created_at = datetime.strptime(p["reg"], "%Y-%m-%d")
            except Exception:
                created_at = None
        user = _ensure_user(
            db,
            username=b.username,
            password=f"bot:{b.username}:{datetime.utcnow().timestamp()}",
            gender=b.gender,
            is_admin=b.is_admin,
            created_at=created_at,
        )
        profile = user.profile
        if profile:
            profile.avatar = p.get("av") or profile.avatar
            profile.city = p.get("city") or profile.city
            profile.sig = p.get("sig") or profile.sig
            profile.age = p.get("age") or profile.age
            profile.oicq = p.get("oicq") or profile.oicq
            profile.email = p.get("email") or profile.email
            db.add(profile)
            db.commit()

    bot_user_ids = [
        u.id for u in db.execute(select(models.User).where(models.User.username.in_([b.username for b in bots]))).scalars().all()
    ]

    # Seed guestbook posts/replies (append only once)
    bot_post_count = (
        db.execute(
            select(func.count())
            .select_from(models.GuestbookPost)
            .where(models.GuestbookPost.user_id.in_(bot_user_ids))
        ).scalar_one()
        if bot_user_ids
        else 0
    )
    if bot_post_count == 0:
        name_to_user = {
            u.username: u for u in db.execute(select(models.User)).scalars().all()
        }
        for post in gb_msgs:
            author = name_to_user.get(post.get("nk"))
            if not author:
                author = _ensure_user(db, post.get("nk", "Guest"), "seed", post.get("g", "secret"))
            created_at = _parse_datetime(post.get("ti", "2001-01-01 00:00:00"))
            p = models.GuestbookPost(
                user_id=author.id,
                mood=post.get("mo") or "😊",
                subject=post.get("su") or "",
                content=post.get("co") or "",
                created_at=created_at,
            )
            db.add(p)
            db.flush()
            for rep in post.get("re") or []:
                rauthor = name_to_user.get(rep.get("nk"))
                if not rauthor:
                    rauthor = _ensure_user(db, rep.get("nk", "Guest"), "seed", rep.get("g", "secret"))
                    name_to_user[rauthor.username] = rauthor
                r_created = _parse_datetime(rep.get("ti", "2001-01-01 00:00:00"))
                db.add(
                    models.GuestbookReply(
                        post_id=p.id,
                        user_id=rauthor.id,
                        content=rep.get("co") or "",
                        created_at=r_created,
                    )
                )
            db.commit()

    # Seed chat history with some bot messages (append only once)
    bot_chat_count = (
        db.execute(
            select(func.count())
            .select_from(models.ChatMessage)
            .where(models.ChatMessage.user_id.in_(bot_user_ids))
        ).scalar_one()
        if bot_user_ids
        else 0
    )
    if bot_chat_count == 0:
        name_to_user = {
            u.username: u for u in db.execute(select(models.User)).scalars().all()
        }
        base = datetime.utcnow() - timedelta(minutes=30)
        idx = 0
        for msg in bot_msgs[:40]:
            bot = bots[idx % len(bots)]
            u = name_to_user.get(bot.username)
            if not u:
                continue
            db.add(
                models.ChatMessage(
                    user_id=u.id,
                    content=msg,
                    color=bot.color,
                    style="normal",
                    target_user_id=None,
                    is_action=False,
                    is_system=False,
                    created_at=base + timedelta(seconds=idx * 20),
                )
            )
            idx += 1
        db.commit()
