from unittest.mock import MagicMock, patch

import pytest

from gemini_client import GeminiClient, load_knowledge


def test_load_knowledge_concatenates_markdown_files(tmp_path):
    (tmp_path / "a.md").write_text("content A", encoding="utf-8")
    (tmp_path / "b.md").write_text("content B", encoding="utf-8")
    (tmp_path / "ignore.txt").write_text("not markdown", encoding="utf-8")

    result = load_knowledge(tmp_path)

    assert "content A" in result
    assert "content B" in result
    assert "not markdown" not in result


def test_generate_draft_returns_text():
    with patch("gemini_client.genai.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.models.generate_content.return_value = MagicMock(text="生成された草稿")
        mock_client_cls.return_value = mock_instance

        client = GeminiClient(api_key="fake-key", knowledge="型データ")
        result = client.generate_draft("今日試したこと")

        assert result == "生成された草稿"
        mock_instance.models.generate_content.assert_called_once()
        _, call_kwargs = mock_instance.models.generate_content.call_args
        assert call_kwargs["contents"] == "今日試したこと"
        assert "型データ" in call_kwargs["config"].system_instruction


def test_generate_draft_raises_on_empty_response():
    with patch("gemini_client.genai.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.models.generate_content.return_value = MagicMock(text="")
        mock_client_cls.return_value = mock_instance

        client = GeminiClient(api_key="fake-key", knowledge="型データ")

        with pytest.raises(ValueError):
            client.generate_draft("今日試したこと")
