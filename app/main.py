import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.db import init_db, SessionLocal
from app.logging_service import log_event
from app.models.log import LogType
from app.routers import (
    auth, profile, messenger, rooms, moderation,
    admin_users, admin_moderation, admin_logs, admin_settings, admin_wallet,
    wallet, referral, games, auctions, media, events, posts, activity, friends, badges,
)
from app.services.media_service import MEDIA_ROOT

app = FastAPI(title="Neprofesionálové API", version="0.1.0 (v1)")


@app.on_event("startup")
def on_startup():
    init_db()


@app.middleware("http")
async def network_logging_middleware(request: Request, call_next):
    """Loguje každý HTTP request do system_network_LOG /
    system_network_log_ERROR podle výsledného status kódu."""
    start = time.time()
    db = SessionLocal()
    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start) * 1000, 2)
        log_type = (
            LogType.SYSTEM_NETWORK_LOG
            if response.status_code < 400
            else LogType.SYSTEM_NETWORK_LOG_ERROR
        )
        log_event(
            db, log_type,
            action=f"{request.method} {request.url.path}",
            target=str(response.status_code),
            ip_address=request.client.host if request.client else None,
            meta={"duration_ms": duration_ms},
        )
        return response
    finally:
        db.close()


app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(messenger.router)
app.include_router(rooms.router)
app.include_router(moderation.router)
# admin.py (v1-v29) rozdělen na 5 domén podle skutečného obsahu (vA5):
# users / moderátoři místností / logy / nastavení / wallet+výběry. Všechny
# sdílí prefix "/admin", takže API cesty se rozdělením nemění.
app.include_router(admin_users.router)
app.include_router(admin_moderation.router)
app.include_router(admin_logs.router)
app.include_router(admin_settings.router)
app.include_router(admin_wallet.router)
app.include_router(wallet.router)
app.include_router(referral.router)
app.include_router(games.router)
app.include_router(auctions.router)
app.include_router(media.router)
app.include_router(events.router)
app.include_router(posts.router)
app.include_router(activity.router)
app.include_router(friends.router)
app.include_router(badges.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": app.version}


# Jednosouborový/statický frontend (design template systém — v17+).
# html=True servíruje /app/appearance.html i /app/ (od v17-BUG-02 opraveno přidáním index.html).
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

# Nahraná média z Galerie médií (app/services/media_service.py) - servírováno
# staticky, bez auth (stejně jako zbytek frontendu v této MVP fázi).
app.mount("/media-files", StaticFiles(directory=str(MEDIA_ROOT)), name="media-files")


@app.get("/", include_in_schema=False)
def root_redirect():
    """Kořenová URL přesměruje rovnou na frontend — v17-BUG-02: dřív / i /app/ vracely 404."""
    return RedirectResponse(url="/app/")
