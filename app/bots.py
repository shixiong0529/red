from __future__ import annotations

import asyncio
import ast
import random
import re
from pathlib import Path
from typing import Callable

from sqlalchemy import select

from . import models
from .crud import save_chat_message
from .db import SessionLocal


BOT_NAMES = {
    "飞翔的鱼",
    "薰衣草",
    "追梦人",
    "小雨点",
    "天涯浪子",
    "月光女孩",
    "蓝色心情",
    "樱花雪",
    "风一样的少年",
    "紫丁香",
    "独行侠",
    "★管理员★",
}

def _load_from_bak() -> tuple[list[str], dict[str, str]]:
    try:
        text = Path("bak/red-dragonfly-chatroom.html").read_text("utf-8", errors="replace")
        m1 = re.search(r"var botMsgs=\[(.*?)\];", text, re.S)
        msgs = ast.literal_eval("[" + (m1.group(1) if m1 else "") + "]") if m1 else []
        m2 = re.search(r"var bots=\[(.*?)\];", text, re.S)
        colors: dict[str, str] = {}
        if m2:
            blob = "[" + m2.group(1) + "]"
            blob = re.sub(r"([\{,]\s*)([a-zA-Z_]\w*)\s*:", r"\1'\2':", blob)
            bots = ast.literal_eval(blob)
            for b in bots:
                if b.get("n") and b.get("c"):
                    colors[str(b["n"])] = str(b["c"])
        return msgs, colors
    except Exception:
        return [], {}


BOT_MSGS, BOT_COLORS = _load_from_bak()


def list_bots(db) -> list[models.User]:
    return db.execute(select(models.User).where(models.User.username.in_(BOT_NAMES))).scalars().all()


async def bot_loop(
    broadcast: Callable[[dict], asyncio.Future],
    should_post: Callable[[], bool],
) -> None:
    # Post a message occasionally when someone is connected.
    while True:
        await asyncio.sleep(random.uniform(3.0, 8.0))
        if not should_post():
            continue
        try:
            db = SessionLocal()
            bots = list_bots(db)
            if not bots:
                continue
            bot = random.choice(bots)
            msg = random.choice(BOT_MSGS) if BOT_MSGS else "大家好！"
            color = BOT_COLORS.get(bot.username, "#00ff00")
            saved = save_chat_message(
                db,
                user_id=bot.id,
                content=msg,
                color=color,
                style="normal",
                target_user_id=None,
                is_action=False,
                is_system=False,
            )
            payload = {
                "type": "message",
                "id": saved.id,
                "user": {
                    "id": bot.id,
                    "username": bot.username,
                    "gender": bot.gender,
                    "is_admin": bot.is_admin,
                },
                "content": msg,
                "color": saved.color,
                "style": saved.style,
                "target_user_id": None,
                "is_action": False,
                "created_at": saved.created_at.isoformat(),
            }
            await broadcast(payload)
        except Exception:
            # Best-effort bots; don't crash the app.
            pass
        finally:
            try:
                db.close()
            except Exception:
                pass
