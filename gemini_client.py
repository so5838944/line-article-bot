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
