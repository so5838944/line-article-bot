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
