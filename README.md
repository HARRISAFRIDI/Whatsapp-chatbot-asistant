# Webora WhatsApp AI Chatbot

A small FastAPI webhook that receives WhatsApp Cloud API text messages, generates
customer-support replies with a LangGraph agent backed by Google Gemini, and sends
the replies through the WhatsApp Cloud API.

## Requirements

- Python 3.10+
- A Meta WhatsApp Cloud API phone number and access token
- A Meta app secret and webhook verify token
- A Google Gemini API key

## Setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set the credentials in `.env`. Keep `.env` private; it is excluded from Git.

## Run locally

```powershell
uvicorn app.main:app --reload
```

Expose the local server with ngrok:

```powershell
ngrok http 8000
```

In the Meta app's WhatsApp webhook settings, use `https://<ngrok-host>/webhook`
as the callback URL and the same `WHATSAPP_VERIFY_TOKEN` as the verify token.
Subscribe the webhook to the `messages` field. Meta's webhook signature is
validated against `WHATSAPP_APP_SECRET`.

The GET `/webhook` endpoint implements Meta's verification challenge. The POST
endpoint accepts text messages, ignores status updates and other unsupported
message types, and responds to each supported incoming text message.

## Tests

Run the webhook tests with:

```powershell
python -m unittest discover -s tests -v
```

## Notes

- The bot currently handles messages independently; it does not persist
  conversation history.
- Configure a durable Meta access token before production use.
- Webhook processing failures return an error so Meta can retry delivery. For a
  production deployment, add persistent idempotency tracking to avoid replying
  twice to retried message events.
