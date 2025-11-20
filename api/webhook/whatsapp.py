from vercel_http import VercelRequest, VercelResponse
import json
from app.db import SessionLocal, engine, Base
from app.services.flows import handle_text_message
from app.config import settings

# Ensure tables exist in serverless context (safe to run on each cold start)
Base.metadata.create_all(bind=engine)


def handler(request: VercelRequest) -> VercelResponse:
    if request.method == "GET":
        mode = request.query.get("hub.mode")
        verify_token = request.query.get("hub.verify_token")
        challenge = request.query.get("hub.challenge", "")
        if mode == "subscribe" and verify_token == settings.wa_verify_token:
            return VercelResponse(challenge, status=200, headers={"Content-Type": "text/plain"})
        return VercelResponse("forbidden", status=403)

    if request.method == "POST":
        try:
            payload = request.json()
        except Exception:
            payload = {}

        db = SessionLocal()
        try:
            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    for m in messages:
                        from_phone = m.get("from")
                        mtype = m.get("type")
                        text = None
                        if mtype == "text":
                            text = m.get("text", {}).get("body", "")
                        elif mtype == "button":
                            text = m.get("button", {}).get("text", "")
                        elif mtype == "interactive":
                            interactive = m.get("interactive", {})
                            button_reply = interactive.get("button_reply")
                            list_reply = interactive.get("list_reply")
                            if button_reply:
                                text = button_reply.get("title")
                            if list_reply:
                                text = list_reply.get("title")
                        if text and from_phone:
                            handle_text_message(db, from_phone, text)
        finally:
            db.close()

        return VercelResponse(json.dumps({"success": True}), status=200, headers={"Content-Type": "application/json"})

    return VercelResponse("method not allowed", status=405)

