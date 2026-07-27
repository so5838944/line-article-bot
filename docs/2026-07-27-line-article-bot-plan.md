# LINE Article Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI service that receives LINE text messages, generates an X-article draft via the Gemini API using Sora's theme templates and tone rules, and replies in LINE.

**Architecture:** LINE Messaging API webhook → FastAPI endpoint → knowledge loader (reads local `knowledge/*.md`) → Gemini API (single call with knowledge as system instruction) → LINE Reply API. Stateless, single request/response cycle per message. No database.

**Tech Stack:** Python, FastAPI, uvicorn, httpx, google-genai (Gemini SDK), python-dotenv, pytest, Railway (nixpacks deploy).

---

## Reference design doc

`C:/Sora Osawa/05_開発部/05_06_line-article-bot/docs/2026-07-27-line-article-bot-design.md`

## File Structure

```
05_開発部/05_06_line-article-bot/
├── config.py
├── line_client.py
├── gemini_client.py
├── main.py
├── requirements.txt
├── railway.toml
├── .env.example
├── .gitignore
├── knowledge/
│   ├── テーマ別記事_型.md
│   ├── 発信哲学.md
│   ├── NGルール.md
│   └── 属人性.md
├── docs/
│   ├── 2026-07-27-line-article-bot-design.md
│   └── 2026-07-27-line-article-bot-plan.md
└── tests/
    ├── conftest.py
    ├── test_config.py
    ├── test_line_client.py
    ├── test_gemini_client.py
    └── test_main.py
```

---

### Task 1: Project scaffolding

**Files:**
- Create: `05_開発部/05_06_line-article-bot/requirements.txt`
- Create: `05_開発部/05_06_line-article-bot/.gitignore`
- Create: `05_開発部/05_06_line-article-bot/.env.example`
- Create: `05_開発部/05_06_line-article-bot/railway.toml`
- Create: `05_開発部/05_06_line-article-bot/knowledge/テーマ別記事_型.md` (copy)
- Create: `05_開発部/05_06_line-article-bot/knowledge/発信哲学.md` (copy)
- Create: `05_開発部/05_06_line-article-bot/knowledge/NGルール.md` (copy)
- Create: `05_開発部/05_06_line-article-bot/knowledge/属人性.md` (empty placeholder)

- [ ] **Step 1: Create `requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
httpx==0.27.2
python-dotenv==1.0.1
google-genai==0.3.0
pytest==7.4.0
```

- [ ] **Step 2: Create `.gitignore`**

```
__pycache__/
*.pyc
.env
.pytest_cache/
```

- [ ] **Step 3: Create `.env.example`**

```
LINE_CHANNEL_SECRET=
LINE_CHANNEL_ACCESS_TOKEN=
GEMINI_API_KEY=
```

- [ ] **Step 4: Create `railway.toml`**

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "on_failure"
```

- [ ] **Step 5: Copy knowledge files**

Copy the current content of these three files verbatim into `knowledge/`:
- `01_SNS運用部/01_01_X課/01_01_02_Article/01_01_02_03_テンプレート/テーマ別記事_型.md` → `knowledge/テーマ別記事_型.md`
- `00_経営企画室/共通ルール/発信哲学・信念/発信哲学.md` → `knowledge/発信哲学.md`
- `00_経営企画室/共通ルール/NGルール/NGルール.md` → `knowledge/NGルール.md`

Create `knowledge/属人性.md` as an empty file with just this line:

```markdown
# 属人性（未定義）
```

- [ ] **Step 6: Initialize git and make first commit**

```bash
cd "05_開発部/05_06_line-article-bot"
git init
git add .
git commit -m "chore: scaffold line-article-bot project"
```

---

### Task 2: config.py — environment variable loading

**Files:**
- Create: `05_開発部/05_06_line-article-bot/config.py`
- Test: `05_開発部/05_06_line-article-bot/tests/conftest.py`
- Test: `05_開発部/05_06_line-article-bot/tests/test_config.py`

- [ ] **Step 1: Create `tests/conftest.py` with default test env vars**

```python
import os

os.environ.setdefault("LINE_CHANNEL_SECRET", "test-secret")
os.environ.setdefault("LINE_CHANNEL_ACCESS_TOKEN", "test-token")
os.environ.setdefault("GEMINI_API_KEY", "test-key")
```

- [ ] **Step 2: Write the failing test**

`tests/test_config.py`:

```python
import importlib

import pytest


def test_loads_when_env_vars_present(monkeypatch):
    monkeypatch.setenv("LINE_CHANNEL_SECRET", "secret")
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "token")
    monkeypatch.setenv("GEMINI_API_KEY", "key")

    import config
    importlib.reload(config)

    assert config.LINE_CHANNEL_SECRET == "secret"
    assert config.LINE_CHANNEL_ACCESS_TOKEN == "token"
    assert config.GEMINI_API_KEY == "key"


def test_raises_when_env_vars_missing(monkeypatch):
    monkeypatch.delenv("LINE_CHANNEL_SECRET", raising=False)
    monkeypatch.delenv("LINE_CHANNEL_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    import config
    with pytest.raises(EnvironmentError):
        importlib.reload(config)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_config.py -v` (from inside `05_06_line-article-bot/`)
Expected: FAIL with `ModuleNotFoundError: No module named 'config'`

- [ ] **Step 4: Write `config.py`**

```python
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
git add config.py tests/conftest.py tests/test_config.py
git commit -m "feat: add config module with required env var validation"
```

---

### Task 3: line_client.py — signature verification

**Files:**
- Create: `05_開発部/05_06_line-article-bot/line_client.py`
- Test: `05_開発部/05_06_line-article-bot/tests/test_line_client.py`

- [ ] **Step 1: Write the failing test**

`tests/test_line_client.py`:

```python
import base64
import hashlib
import hmac

from line_client import verify_signature


def _sign(secret: str, body: bytes) -> str:
    hash_value = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(hash_value).decode("utf-8")


def test_verify_signature_accepts_valid_signature():
    secret = "test-secret"
    body = b'{"events": []}'
    signature = _sign(secret, body)

    assert verify_signature(secret, body, signature) is True


def test_verify_signature_rejects_invalid_signature():
    secret = "test-secret"
    body = b'{"events": []}'

    assert verify_signature(secret, body, "not-a-valid-signature") is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_line_client.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'line_client'`

- [ ] **Step 3: Write `line_client.py` (signature part only)**

```python
import base64
import hashlib
import hmac

import httpx

LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"


def verify_signature(channel_secret: str, body: bytes, signature: str) -> bool:
    hash_value = hmac.new(channel_secret.encode("utf-8"), body, hashlib.sha256).digest()
    expected_signature = base64.b64encode(hash_value).decode("utf-8")
    return hmac.compare_digest(expected_signature, signature)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_line_client.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add line_client.py tests/test_line_client.py
git commit -m "feat: add LINE webhook signature verification"
```

---

### Task 4: line_client.py — reply sending

**Files:**
- Modify: `05_開発部/05_06_line-article-bot/line_client.py`
- Modify: `05_開発部/05_06_line-article-bot/tests/test_line_client.py`

- [ ] **Step 1: Add the failing test**

Append to `tests/test_line_client.py`:

```python
from unittest.mock import MagicMock, patch

from line_client import reply_message


def test_reply_message_sends_correct_payload():
    with patch("line_client.httpx.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)

        reply_message("token123", "reply-token-abc", "こんにちは")

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == LINE_REPLY_URL
        assert kwargs["headers"]["Authorization"] == "Bearer token123"
        assert kwargs["json"]["replyToken"] == "reply-token-abc"
        assert kwargs["json"]["messages"][0] == {"type": "text", "text": "こんにちは"}
```

Add this import at the top of `tests/test_line_client.py`:

```python
from line_client import LINE_REPLY_URL
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_line_client.py -v`
Expected: FAIL with `ImportError: cannot import name 'reply_message'`

- [ ] **Step 3: Add `reply_message` to `line_client.py`**

Append to `line_client.py`:

```python
def reply_message(channel_access_token: str, reply_token: str, text: str) -> None:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {channel_access_token}",
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}],
    }
    response = httpx.post(LINE_REPLY_URL, headers=headers, json=payload, timeout=10.0)
    response.raise_for_status()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_line_client.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add line_client.py tests/test_line_client.py
git commit -m "feat: add LINE reply message sending"
```

---

### Task 5: gemini_client.py — knowledge loader

**Files:**
- Create: `05_開発部/05_06_line-article-bot/gemini_client.py`
- Test: `05_開発部/05_06_line-article-bot/tests/test_gemini_client.py`

- [ ] **Step 1: Write the failing test**

`tests/test_gemini_client.py`:

```python
from gemini_client import load_knowledge


def test_load_knowledge_concatenates_markdown_files(tmp_path):
    (tmp_path / "a.md").write_text("content A", encoding="utf-8")
    (tmp_path / "b.md").write_text("content B", encoding="utf-8")
    (tmp_path / "ignore.txt").write_text("not markdown", encoding="utf-8")

    result = load_knowledge(tmp_path)

    assert "content A" in result
    assert "content B" in result
    assert "not markdown" not in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_gemini_client.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'gemini_client'`

- [ ] **Step 3: Write `gemini_client.py` (loader part only)**

```python
import os
from pathlib import Path

from google import genai
from google.genai import types

DEFAULT_KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"


def load_knowledge(knowledge_dir: Path = DEFAULT_KNOWLEDGE_DIR) -> str:
    parts = []
    for filename in sorted(os.listdir(knowledge_dir)):
        if filename.endswith(".md"):
            content = (Path(knowledge_dir) / filename).read_text(encoding="utf-8")
            parts.append(f"## {filename}\n\n{content}")
    return "\n\n---\n\n".join(parts)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_gemini_client.py -v`
Expected: PASS (1 test)

- [ ] **Step 5: Commit**

```bash
git add gemini_client.py tests/test_gemini_client.py
git commit -m "feat: add knowledge file loader"
```

---

### Task 6: gemini_client.py — draft generation

**Files:**
- Modify: `05_開発部/05_06_line-article-bot/gemini_client.py`
- Modify: `05_開発部/05_06_line-article-bot/tests/test_gemini_client.py`

- [ ] **Step 1: Add the failing tests**

Append to `tests/test_gemini_client.py`:

```python
from unittest.mock import MagicMock, patch

import pytest

from gemini_client import GeminiClient


def test_generate_draft_returns_text():
    with patch("gemini_client.genai.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.models.generate_content.return_value = MagicMock(text="生成された草稿")
        mock_client_cls.return_value = mock_instance

        client = GeminiClient(api_key="fake-key", knowledge="型データ")
        result = client.generate_draft("今日試したこと")

        assert result == "生成された草稿"
        mock_instance.models.generate_content.assert_called_once()


def test_generate_draft_raises_on_empty_response():
    with patch("gemini_client.genai.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.models.generate_content.return_value = MagicMock(text="")
        mock_client_cls.return_value = mock_instance

        client = GeminiClient(api_key="fake-key", knowledge="型データ")

        with pytest.raises(ValueError):
            client.generate_draft("今日試したこと")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_gemini_client.py -v`
Expected: FAIL with `ImportError: cannot import name 'GeminiClient'`

- [ ] **Step 3: Add `GeminiClient` to `gemini_client.py`**

Append to `gemini_client.py`:

```python
SYSTEM_INSTRUCTION_HEADER = (
    "あなたはSNSマーケターのSora（澤空）のX記事下書き作成アシスタントです。"
    "以下のテーマ別記事の型・発信哲学・NGルールを踏まえて、"
    "ユーザーが送ってきたメモの内容から最も適したテーマの型を1つ選び、"
    "その型に沿って記事を生成してください。"
    "どのテーマを選んだかの説明は不要です。完成した記事本文だけを出力してください。\n\n"
)


class GeminiClient:
    def __init__(self, api_key: str, knowledge: str):
        self._client = genai.Client(api_key=api_key)
        self._system_instruction = SYSTEM_INSTRUCTION_HEADER + knowledge

    def generate_draft(self, memo: str) -> str:
        response = self._client.models.generate_content(
            model="gemini-3.5-flash",
            contents=memo,
            config=types.GenerateContentConfig(
                system_instruction=self._system_instruction,
            ),
        )
        if not response.text:
            raise ValueError("Gemini returned empty response")
        return response.text
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_gemini_client.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add gemini_client.py tests/test_gemini_client.py
git commit -m "feat: add Gemini draft generation"
```

---

### Task 7: main.py — FastAPI webhook endpoint

**Files:**
- Create: `05_開発部/05_06_line-article-bot/main.py`
- Test: `05_開発部/05_06_line-article-bot/tests/test_main.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_main.py`:

```python
import base64
import hashlib
import hmac
import json
from unittest.mock import patch

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def _signature_headers(body: bytes) -> dict:
    hash_value = hmac.new(
        main.LINE_CHANNEL_SECRET.encode("utf-8"), body, hashlib.sha256
    ).digest()
    signature = base64.b64encode(hash_value).decode("utf-8")
    return {"X-Line-Signature": signature}


def test_webhook_rejects_invalid_signature():
    body = json.dumps({"events": []}).encode("utf-8")

    response = client.post(
        "/webhook", content=body, headers={"X-Line-Signature": "invalid"}
    )

    assert response.status_code == 401


def test_webhook_replies_with_draft_for_text_message():
    body = json.dumps({
        "events": [{
            "type": "message",
            "replyToken": "reply-token-abc",
            "message": {"type": "text", "text": "今日フォロワーが伸びた話"},
        }]
    }).encode("utf-8")

    with patch.object(
        main.gemini_client, "generate_draft", return_value="生成された草稿"
    ) as mock_generate, patch("main.reply_message") as mock_reply:
        response = client.post("/webhook", content=body, headers=_signature_headers(body))

    assert response.status_code == 200
    mock_generate.assert_called_once_with("今日フォロワーが伸びた話")
    mock_reply.assert_called_once_with(
        main.LINE_CHANNEL_ACCESS_TOKEN, "reply-token-abc", "生成された草稿"
    )


def test_webhook_asks_for_text_when_message_is_not_text():
    body = json.dumps({
        "events": [{
            "type": "message",
            "replyToken": "reply-token-abc",
            "message": {"type": "image"},
        }]
    }).encode("utf-8")

    with patch("main.reply_message") as mock_reply:
        response = client.post("/webhook", content=body, headers=_signature_headers(body))

    assert response.status_code == 200
    mock_reply.assert_called_once_with(
        main.LINE_CHANNEL_ACCESS_TOKEN, "reply-token-abc", "テキストで送ってください。"
    )


def test_webhook_asks_for_more_detail_when_message_too_short():
    body = json.dumps({
        "events": [{
            "type": "message",
            "replyToken": "reply-token-abc",
            "message": {"type": "text", "text": "ok"},
        }]
    }).encode("utf-8")

    with patch("main.reply_message") as mock_reply:
        response = client.post("/webhook", content=body, headers=_signature_headers(body))

    assert response.status_code == 200
    mock_reply.assert_called_once_with(
        main.LINE_CHANNEL_ACCESS_TOKEN, "reply-token-abc", "もう少し詳しく送ってください。"
    )


def test_webhook_replies_with_error_message_when_gemini_fails():
    body = json.dumps({
        "events": [{
            "type": "message",
            "replyToken": "reply-token-abc",
            "message": {"type": "text", "text": "今日フォロワーが伸びた話"},
        }]
    }).encode("utf-8")

    with patch.object(
        main.gemini_client, "generate_draft", side_effect=RuntimeError("boom")
    ), patch("main.reply_message") as mock_reply:
        response = client.post("/webhook", content=body, headers=_signature_headers(body))

    assert response.status_code == 200
    mock_reply.assert_called_once_with(
        main.LINE_CHANNEL_ACCESS_TOKEN,
        "reply-token-abc",
        "生成に失敗しました。もう一度送ってください。",
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_main.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'main'`

- [ ] **Step 3: Write `main.py`**

```python
from fastapi import FastAPI, HTTPException, Request

from config import GEMINI_API_KEY, LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET
from gemini_client import GeminiClient, load_knowledge
from line_client import reply_message, verify_signature

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
            reply_message(LINE_CHANNEL_ACCESS_TOKEN, reply_token, GENERATION_FAILED_REPLY)
            continue

        reply_message(LINE_CHANNEL_ACCESS_TOKEN, reply_token, draft)

    return {"status": "ok"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_main.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Run the full test suite**

Run: `pytest -v` (from `05_06_line-article-bot/`)
Expected: All tests across all files PASS

- [ ] **Step 6: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add LINE webhook endpoint wiring signature check, Gemini, and reply"
```

---

### Task 8: Deployment

**Files:**
- Create: `05_開発部/05_06_line-article-bot/README.md`

- [ ] **Step 1: Write `README.md` with setup and deployment instructions**

```markdown
# line-article-bot

SoraがLINEに送ったメモを、X記事の型（`knowledge/テーマ別記事_型.md`）に沿ってGemini APIで整形し、LINEに返信するBot。

## ローカル実行

\`\`\`bash
pip install -r requirements.txt
cp .env.example .env
# .env にLINE_CHANNEL_SECRET / LINE_CHANNEL_ACCESS_TOKEN / GEMINI_API_KEY を設定
uvicorn main:app --reload
\`\`\`

## テスト

\`\`\`bash
pytest -v
\`\`\`

## Railwayへのデプロイ

1. このディレクトリのリポジトリをGitHubにpushする
2. Railwayで新規プロジェクトを作成し、そのGitHubリポジトリを接続する
3. Railwayの環境変数に `LINE_CHANNEL_SECRET` / `LINE_CHANNEL_ACCESS_TOKEN` / `GEMINI_API_KEY` を設定する
4. デプロイ完了後に発行されるURL + `/webhook` を、LINE Developersコンソールの Webhook URL に設定する
5. LINE Developersコンソールで「Webhookの利用」をONにする

## 属人性ファイルの更新

`knowledge/属人性.md` の中身が確定したら、このファイルを上書きしてRailwayに再デプロイする（git push で自動反映）。
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add setup and deployment instructions"
```

- [ ] **Step 3: Manual verification (not automatable — requires real LINE/Gemini credentials)**

1. Soraが用意した `LINE_CHANNEL_SECRET` / `LINE_CHANNEL_ACCESS_TOKEN` / `GEMINI_API_KEY` を Railway の環境変数に設定する
2. GitHubリポジトリを作成しpush、RailwayでそのリポジトリからデプロイURLを発行する
3. LINE DevelopersコンソールのWebhook URLに `{デプロイURL}/webhook` を設定し、Webhook利用をONにする
4. Soraの個人LINEから、そのLINE公式アカウントに実際にメモを送り、テーマに沿った草稿が返ってくることを確認する

---

## Self-review notes

- Spec coverage: テキストのみ対応／送信者制限なし／自動テーマ判定／LINE返信のみ／属人性は空ファイル — すべてTask 1〜7でカバー
- No placeholders — all code blocks are complete and runnable
- Naming consistency checked: `verify_signature`, `reply_message`, `load_knowledge`, `GeminiClient.generate_draft` used consistently across all tasks
