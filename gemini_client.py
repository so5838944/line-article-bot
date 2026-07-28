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
