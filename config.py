import os

from dotenv import load_dotenv

load_dotenv()

LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

missing = [k for k, v in {
    "LINE_CHANNEL_SECRET": LINE_CHANNEL_SECRET,
    "LINE_CHANNEL_ACCESS_TOKEN": LINE_CHANNEL_ACCESS_TOKEN,
    "GEMINI_API_KEY": GEMINI_API_KEY,
}.items() if not v]

if missing:
    raise EnvironmentError(f"環境変数が設定されていません: {', '.join(missing)}")
