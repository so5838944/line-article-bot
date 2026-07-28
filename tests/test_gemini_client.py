from gemini_client import load_knowledge


def test_load_knowledge_concatenates_markdown_files(tmp_path):
    (tmp_path / "a.md").write_text("content A", encoding="utf-8")
    (tmp_path / "b.md").write_text("content B", encoding="utf-8")
    (tmp_path / "ignore.txt").write_text("not markdown", encoding="utf-8")

    result = load_knowledge(tmp_path)

    assert "content A" in result
    assert "content B" in result
    assert "not markdown" not in result
