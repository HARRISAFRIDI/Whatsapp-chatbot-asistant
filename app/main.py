import hashlib
import hmac
import json
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request, Response
from starlette.concurrency import run_in_threadpool

from app.agent import generate_reply
from app.config import settings
from app.whatsapp import send_message

app = FastAPI(title="Webora WhatsApp AI Chatbot")


def is_valid_signature(body: bytes, signature: str | None) -> bool:
    if not settings.whatsapp_app_secret or not signature:
        return False
    expected = "sha256=" + hmac.new(
        settings.whatsapp_app_secret.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def extract_messages(payload: dict[str, Any]) -> list[tuple[str, str]]:
    messages: list[tuple[str, str]] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                text = message.get("text", {}).get("body")
                sender = message.get("from")
                if isinstance(sender, str) and isinstance(text, str) and text.strip():
                    messages.append((sender, text.strip()))
    return messages


@app.get("/webhook")
async def verify_webhook(
    mode: str | None = Query(default=None, alias="hub.mode"),
    verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> Response:
    if (
        mode != "subscribe"
        or not settings.whatsapp_verify_token
        or not verify_token
        or not hmac.compare_digest(verify_token, settings.whatsapp_verify_token)
        or challenge is None
    ):
        raise HTTPException(status_code=403, detail="Webhook verification failed.")
    return Response(content=challenge, media_type="text/plain")


@app.post("/webhook")
async def receive_webhook(request: Request) -> dict[str, str]:
    body = await request.body()
    if not is_valid_signature(body, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status_code=401, detail="Invalid webhook signature.")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Webhook payload must be a JSON object.")

    for sender, text in extract_messages(payload):
        reply = await run_in_threadpool(generate_reply, text)
        await send_message(sender, reply)
    return {"status": "ok"}
