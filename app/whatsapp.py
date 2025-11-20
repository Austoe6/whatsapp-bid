import httpx
from typing import Iterable
from .config import settings

GRAPH_BASE = "https://graph.facebook.com/v20.0"


def _messages_url() -> str:
    return f"{GRAPH_BASE}/{settings.wa_phone_number_id}/messages"


def send_text(to_phone: str, body: str) -> None:
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"preview_url": False, "body": body},
    }
    headers = {
        "Authorization": f"Bearer {settings.wa_access_token}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=20.0) as client:
        client.post(_messages_url(), headers=headers, json=payload)


def broadcast_text(recipients: Iterable[str], body: str) -> None:
    for phone in recipients:
        send_text(phone, body)