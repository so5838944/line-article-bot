import logging

from fastapi import FastAPI, HTTPException, Request

from config import GEMINI_API_KEY, LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET
from gemini_client import GeminiClient, load_knowledge
from line_client import reply_message, verify_signature

logger = logging.getLogger(__name__)

app = FastAPI()
gemini_client = GeminiClient(api_key=GEMINI_API_KEY, knowledge=load_knowledge())

MIN_MESSAGE_LENGTH = 5
NOT_TEXT_REPLY = "テキストで送ってください。"
TOO_SHORT_REPLY = "もう少し詳しく送ってください。"
GENERATION_FAILED_REPLY = "生成に失敗しました。もう一度送ってください。"


@app.post("/webhook")
async def webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")

    if not verify_signature(LINE_CHANNEL_SECRET, body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()

    for event in payload.get("events", []):
        if event.get("type") != "message":
            continue

        reply_token = event["replyToken"]
        message = event["message"]

        if message.get("type") != "text":
            reply_message(LINE_CHANNEL_ACCESS_TOKEN, reply_token, NOT_TEXT_REPLY)
            continue

        text = message.get("text", "").strip()
        if len(text) < MIN_MESSAGE_LENGTH:
            reply_message(LINE_CHANNEL_ACCESS_TOKEN, reply_token, TOO_SHORT_REPLY)
            continue

        try:
            draft = gemini_client.generate_draft(text)
        except Exception:
            logger.exception("Gemini draft generation failed")
            reply_message(LINE_CHANNEL_ACCESS_TOKEN, reply_token, GENERATION_FAILED_REPLY)
            continue

        reply_message(LINE_CHANNEL_ACCESS_TOKEN, reply_token, draft)

    return {"status": "ok"}
