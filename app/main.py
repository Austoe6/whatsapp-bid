from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from .config import settings
from .db import Base, engine, SessionLocal
from .services.flows import handle_text_message

app = FastAPI(title="WhatsApp Bid App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    # Avoid writing to read-only FS on serverless. Only auto-create for local sqlite.
    try:
        from .config import settings as _s
        if _s.database_url.startswith("sqlite"):
            Base.metadata.create_all(bind=engine)
    except Exception:
        # Suppress startup errors to keep webhook verification working
        pass


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/webhook/whatsapp")
def whatsapp_verify(request: Request):
    # Meta sends hub.mode, hub.verify_token, hub.challenge
    qp = request.query_params
    mode = qp.get("hub.mode") or qp.get("mode")
    verify_token = qp.get("hub.verify_token") or qp.get("verify_token")
    challenge = qp.get("hub.challenge") or qp.get("challenge") or ""

    if mode == "subscribe" and verify_token == settings.wa_verify_token:
        return PlainTextResponse(challenge, status_code=200)
    return PlainTextResponse("forbidden", status_code=403)


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    # Parse messages: entry -> changes -> value -> messages
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            for m in messages:
                from_phone = m.get("from")
                mtype = m.get("type")
                if mtype == "text":
                    text = m.get("text", {}).get("body", "")
                    if from_phone:
                        handle_text_message(db, from_phone, text)
                elif mtype == "button":
                    # Handle interactive button postbacks if used later
                    text = m.get("button", {}).get("text", "")
                    if from_phone:
                        handle_text_message(db, from_phone, text)
                elif mtype == "interactive":
                    # List/Reply selections can be mapped to text commands
                    interactive = m.get("interactive", {})
                    button_reply = interactive.get("button_reply")
                    list_reply = interactive.get("list_reply")
                    text = None
                    if button_reply:
                        text = button_reply.get("title")
                    if list_reply:
                        text = list_reply.get("title")
                    if text and from_phone:
                        handle_text_message(db, from_phone, text)
    return {"success": True}