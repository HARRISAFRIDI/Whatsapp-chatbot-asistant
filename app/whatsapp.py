import httpx

from app.config import settings


async def send_message(to: str, message: str) -> None:
    if not settings.whatsapp_access_token:
        raise RuntimeError("WHATSAPP_ACCESS_TOKEN must be configured before sending messages.")
    if not settings.whatsapp_phone_number_id:
        raise RuntimeError("WHATSAPP_PHONE_NUMBER_ID must be configured before sending messages.")

    url = (
        f"https://graph.facebook.com/{settings.graph_api_version}/"
        f"{settings.whatsapp_phone_number_id}/messages"
    )
    headers = {"Authorization": f"Bearer {settings.whatsapp_access_token}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
