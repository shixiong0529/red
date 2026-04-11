from __future__ import annotations

import json
from typing import Dict, List

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect


class ConnectionManager:
    def __init__(self) -> None:
        self.active: Dict[int, List[WebSocket]] = {}
        self.users: Dict[int, dict] = {}

    async def connect(self, user: dict, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.setdefault(user["id"], []).append(websocket)
        self.users[user["id"]] = user

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        conns = self.active.get(user_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self.active.pop(user_id, None)
            self.users.pop(user_id, None)

    async def broadcast(self, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False)
        for user_id, conns in list(self.active.items()):
            for ws in list(conns):
                try:
                    await ws.send_text(data)
                except Exception:
                    self.disconnect(user_id, ws)

    async def send_to(self, user_id: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False)
        for ws in list(self.active.get(user_id, [])):
            try:
                await ws.send_text(data)
            except Exception:
                self.disconnect(user_id, ws)

    def list_users(self) -> List[dict]:
        return list(self.users.values())
