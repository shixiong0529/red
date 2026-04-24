from __future__ import annotations

import json
from datetime import datetime
from typing import List

from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .config import app_settings
from .db import Base, engine
from .deps import get_db, get_current_user, require_user
from .security import session_expiry
from .ws import ConnectionManager
from .seed import seed_if_needed
from .bots import BOT_NAMES, list_bots, bot_loop

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

manager = ConnectionManager()


def cookie_domain_for_request(request: Request) -> str | None:
    configured = app_settings.session_cookie_domain
    if not configured:
        return None
    host = (request.url.hostname or "").lower().rstrip(".")
    domain = configured.lower().lstrip(".").rstrip(".")
    if host == domain or host.endswith("." + domain):
        return configured
    return None


def set_session_cookie(response: JSONResponse, request: Request, token: str) -> None:
    response.set_cookie(
        app_settings.session_cookie_name,
        token,
        httponly=True,
        samesite=app_settings.session_cookie_samesite,
        secure=app_settings.session_cookie_secure,
        domain=cookie_domain_for_request(request),
    )


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    # Seed demo bots + content from bak/ on first run.
    from .db import SessionLocal

    db = SessionLocal()
    try:
        seed_if_needed(db)
    finally:
        db.close()
    # Background bot chatter (best-effort).
    import asyncio

    async def _broadcast(payload: dict):
        await manager.broadcast(payload)

    asyncio.create_task(bot_loop(_broadcast, lambda: bool(manager.active)))


def page_or_login(request: Request, user, template: str) -> HTMLResponse:
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(template, {"request": request})


@app.get("/", response_class=HTMLResponse)
def index(request: Request, user=Depends(get_current_user)):
    return page_or_login(request, user, "index.html")


@app.get("/guestbook", response_class=HTMLResponse)
def guestbook(request: Request, user=Depends(get_current_user)):
    return page_or_login(request, user, "guestbook.html")


@app.get("/settings", response_class=HTMLResponse)
def settings(request: Request, user=Depends(get_current_user)):
    return page_or_login(request, user, "settings.html")


@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request, user=Depends(get_current_user)):
    return page_or_login(request, user, "profile.html")


@app.get("/help", response_class=HTMLResponse)
def help_page(request: Request, user=Depends(get_current_user)):
    return page_or_login(request, user, "help.html")


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, user=Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Not allowed")
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, user=Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/logout")
def logout(
    request: Request,
    session: str | None = Cookie(default=None, alias=app_settings.session_cookie_name),
    db: Session = Depends(get_db),
):
    if session:
        crud.delete_session(db, session)
    resp = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    resp.delete_cookie(app_settings.session_cookie_name)
    domain = cookie_domain_for_request(request)
    if domain:
        resp.delete_cookie(app_settings.session_cookie_name, domain=domain)
    return resp


@app.post("/api/auth/register")
def register(request: Request, payload: schemas.UserRegister, db: Session = Depends(get_db)):
    if not payload.username.isalnum():
        raise HTTPException(status_code=400, detail="Username must be alphanumeric")
    if len(payload.password) < 4:
        raise HTTPException(status_code=400, detail="Password too short")
    if crud.get_user_by_username(db, payload.username):
        raise HTTPException(status_code=400, detail="Username exists")
    user = crud.create_user(db, payload.username, payload.password, payload.gender)
    sess = crud.create_session(db, user.id)
    resp = {
        "ok": True,
        "user": {"id": user.id, "username": user.username, "gender": user.gender, "is_admin": user.is_admin},
    }
    response = JSONResponse(resp)
    set_session_cookie(response, request, sess.token)
    return response


@app.post("/api/auth/login")
def login(request: Request, payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    sess = crud.create_session(db, user.id)
    resp = {
        "ok": True,
        "user": {"id": user.id, "username": user.username, "gender": user.gender, "is_admin": user.is_admin},
    }
    response = JSONResponse(resp)
    set_session_cookie(response, request, sess.token)
    return response


@app.get("/api/me", response_model=schemas.MeResponse)
def me(user=Depends(get_current_user)):
    if not user:
        return {"user": None}
    return {
        "user": {"id": user.id, "username": user.username, "gender": user.gender, "is_admin": user.is_admin}
    }


@app.get("/api/profile/me", response_model=schemas.ProfileResponse)
def profile_me(user=Depends(require_user)):
    profile = user.profile
    return {
        "user": {"id": user.id, "username": user.username, "gender": user.gender},
        "avatar": profile.avatar if profile else "🐬",
        "city": profile.city if profile else "",
        "email": profile.email if profile else "",
        "oicq": profile.oicq if profile else "",
        "sig": profile.sig if profile else "",
        "age": profile.age if profile else "",
    }


@app.put("/api/profile/me", response_model=schemas.ProfileResponse)
def profile_update(payload: schemas.ProfileUpdate, db: Session = Depends(get_db), user=Depends(require_user)):
    data = payload.model_dump()
    if data.get("username") and not data["username"].isalnum():
        raise HTTPException(status_code=400, detail="Username must be alphanumeric")
    if data.get("email") and "@" not in data["email"]:
        raise HTTPException(status_code=400, detail="Invalid email")
    if data.get("oicq") and not data["oicq"].isdigit():
        raise HTTPException(status_code=400, detail="OICQ must be digits")
    try:
        profile = crud.update_profile(db, user, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {
        "user": {"id": user.id, "username": user.username, "gender": user.gender},
        "avatar": profile.avatar,
        "city": profile.city,
        "email": profile.email,
        "oicq": profile.oicq,
        "sig": profile.sig,
        "age": profile.age,
    }


@app.get("/api/users/{user_id}")
def user_profile(user_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    target = crud.get_user_by_id(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    profile = target.profile
    return {
        "user": {"id": target.id, "username": target.username, "gender": target.gender},
        "avatar": profile.avatar if profile else "🐬",
        "city": profile.city if profile else "",
        "email": profile.email if profile else "",
        "oicq": profile.oicq if profile else "",
        "sig": profile.sig if profile else "",
        "age": profile.age if profile else "",
        "reg": target.created_at.isoformat(),
    }


@app.get("/api/chat/history", response_model=List[schemas.ChatMessageOut])
def chat_history(limit: int = 50, db: Session = Depends(get_db), user=Depends(require_user)):
    msgs = crud.list_chat_messages(db, limit=limit)
    out = []
    for m in msgs:
        out.append(
            {
                "id": m.id,
                "user": {"id": m.user.id, "username": m.user.username, "gender": m.user.gender},
                "content": m.content,
                "color": m.color,
                "style": m.style,
                "target_user_id": m.target_user_id,
                "is_action": m.is_action,
                "is_system": m.is_system,
                "created_at": m.created_at,
            }
        )
    return out


@app.get("/api/chat/online", response_model=List[schemas.OnlineUser])
def chat_online(db: Session = Depends(get_db), user=Depends(require_user)):
    online = {u.id: u for u in crud.online_users(db)}
    for b in list_bots(db):
        online.setdefault(b.id, b)
    return [
        {"id": u.id, "username": u.username, "gender": u.gender, "is_admin": u.is_admin}
        for u in online.values()
    ]


@app.put("/api/chat/room")
def chat_room(room: str, db: Session = Depends(get_db), user=Depends(require_user)):
    crud.set_user_room(db, user.id, room)
    return {"ok": True}


@app.get("/api/guestbook", response_model=List[schemas.GuestbookPostOut])
def guestbook_list(db: Session = Depends(get_db), user=Depends(require_user)):
    posts = crud.list_posts(db)
    out = []
    for p in posts:
        replies = []
        for r in p.replies:
            replies.append(
                {
                    "id": r.id,
                    "user": {"id": r.user.id, "username": r.user.username, "gender": r.user.gender},
                    "content": r.content,
                    "created_at": r.created_at,
                }
            )
        out.append(
            {
                "id": p.id,
                "user": {"id": p.user.id, "username": p.user.username, "gender": p.user.gender},
                "mood": p.mood,
                "subject": p.subject,
                "content": p.content,
                "created_at": p.created_at,
                "replies": replies,
            }
        )
    return out


@app.post("/api/guestbook", response_model=schemas.GuestbookPostOut)
def guestbook_create(payload: schemas.GuestbookPostIn, db: Session = Depends(get_db), user=Depends(require_user)):
    post = crud.create_post(db, user.id, payload.mood, payload.subject, payload.content)
    return {
        "id": post.id,
        "user": {"id": user.id, "username": user.username, "gender": user.gender},
        "mood": post.mood,
        "subject": post.subject,
        "content": post.content,
        "created_at": post.created_at,
        "replies": [],
    }


@app.post("/api/guestbook/{post_id}/reply", response_model=schemas.GuestbookReplyOut)
def guestbook_reply(
    post_id: int, payload: schemas.GuestbookReplyIn, db: Session = Depends(get_db), user=Depends(require_user)
):
    reply = crud.create_reply(db, post_id, user.id, payload.content)
    return {
        "id": reply.id,
        "user": {"id": user.id, "username": user.username, "gender": user.gender},
        "content": reply.content,
        "created_at": reply.created_at,
    }


@app.delete("/api/guestbook/{post_id}")
def guestbook_delete(post_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    ok = crud.delete_post(db, post_id, user.id, user.is_admin)
    if not ok:
        raise HTTPException(status_code=403, detail="Not allowed")
    return {"ok": True}


@app.delete("/api/guestbook/reply/{reply_id}")
def guestbook_reply_delete(reply_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    ok = crud.delete_reply(db, reply_id, user.id, user.is_admin)
    if not ok:
        raise HTTPException(status_code=403, detail="Not allowed")
    return {"ok": True}


@app.get("/api/admin/users")
def admin_users(db: Session = Depends(get_db), user=Depends(require_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Not allowed")
    users = db.execute(
        models.User.__table__.select().order_by(models.User.created_at.desc())
    ).fetchall()
    return [
        {
            "id": u.id,
            "username": u.username,
            "gender": u.gender,
            "is_admin": u.is_admin,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@app.get("/api/admin/posts")
def admin_posts(db: Session = Depends(get_db), user=Depends(require_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Not allowed")
    posts = crud.list_posts(db)
    return [
        {
            "id": p.id,
            "user": {"id": p.user.id, "username": p.user.username},
            "subject": p.subject,
            "content": p.content,
            "created_at": p.created_at.isoformat(),
        }
        for p in posts
    ]


@app.delete("/api/admin/user/{user_id}")
def admin_delete_user(user_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Not allowed")
    if user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete self")
    target = crud.get_user_by_id(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(target)
    db.commit()
    return {"ok": True}


@app.websocket("/ws/chat")
async def chat_ws(
    websocket: WebSocket,
    session: str | None = Cookie(default=None, alias=app_settings.session_cookie_name),
    db: Session = Depends(get_db),
):
    if not session:
        await websocket.close(code=4401)
        return
    sess = crud.get_session(db, session)
    if not sess:
        await websocket.close(code=4401)
        return
    user = sess.user
    crud.touch_session(db, sess)
    user_payload = {"id": user.id, "username": user.username, "gender": user.gender, "is_admin": user.is_admin}
    await manager.connect(user_payload, websocket)
    await manager.broadcast({"type": "online", "users": manager.list_users()})
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            crud.touch_session(db, sess)
            msg_type = data.get("type", "message")
            content = str(data.get("content", "")).strip()
            color = data.get("color", "#00ff00")
            style = data.get("style", "normal")
            target_user_id = data.get("target_user_id")
            is_action = msg_type == "action"
            if not content:
                continue
            saved = crud.save_chat_message(
                db,
                user_id=user.id,
                content=content,
                color=color,
                style=style,
                target_user_id=target_user_id,
                is_action=is_action,
                is_system=False,
            )
            payload = {
                "type": "message",
                "id": saved.id,
                "user": user_payload,
                "content": content,
                "color": color,
                "style": style,
                "target_user_id": target_user_id,
                "is_action": is_action,
                "created_at": saved.created_at.isoformat(),
            }
            if target_user_id:
                await manager.send_to(int(target_user_id), payload)
                await manager.send_to(user.id, payload)
            else:
                await manager.broadcast(payload)
    except WebSocketDisconnect:
        manager.disconnect(user.id, websocket)
        await manager.broadcast({"type": "online", "users": manager.list_users()})
