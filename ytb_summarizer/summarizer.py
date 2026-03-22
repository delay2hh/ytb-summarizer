"""LLM abstraction layer supporting Anthropic, OpenAI, DeepSeek, and custom providers."""
from __future__ import annotations

from typing import Callable


def summarize(
    transcript: str,
    title: str,
    url: str,
    prompt: str,
    provider_config: dict,
    progress_cb: Callable[[str], None] | None = None,
) -> str:
    """
    Call the configured LLM and return the summary markdown.

    provider_config keys:
        provider: "anthropic" | "openai" | "deepseek" | "custom"
        api_key: str
        model: str
        base_url: str (optional, for custom/deepseek)
    """
    provider = provider_config.get("provider", "anthropic")

    if progress_cb:
        progress_cb(f"正在调用 {provider} ({provider_config.get('model', '')})...")

    if provider == "anthropic":
        return _call_anthropic(prompt, provider_config)
    else:
        return _call_openai_compatible(prompt, provider_config)


def _call_anthropic(prompt: str, cfg: dict) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=cfg["api_key"])
    message = client.messages.create(
        model=cfg.get("model", "claude-sonnet-4-6"),
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _call_openai_compatible(prompt: str, cfg: dict) -> str:
    import openai

    kwargs: dict = {"api_key": cfg["api_key"]}

    provider = cfg.get("provider", "openai")
    if provider == "deepseek":
        kwargs["base_url"] = cfg.get("base_url", "https://api.deepseek.com")
    elif provider == "custom":
        base_url = cfg.get("base_url", "")
        if base_url:
            kwargs["base_url"] = base_url

    client = openai.OpenAI(**kwargs)
    response = client.chat.completions.create(
        model=cfg.get("model", "gpt-4o"),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=8192,
    )
    return response.choices[0].message.content


# ── Provider / Model catalog ─────────────────────────────────────────────────

PROVIDER_MODELS: dict[str, list[str]] = {
    "anthropic": [
        "claude-sonnet-4-6",
        "claude-opus-4-6",
        "claude-haiku-4-5-20251001",
        "claude-3-5-sonnet-20241022",
        "claude-3-opus-20240229",
    ],
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "o1-preview",
        "o1-mini",
    ],
    "deepseek": [
        "deepseek-chat",
        "deepseek-reasoner",
    ],
    "custom": [],
}

PROVIDER_NEEDS_BASE_URL = {"deepseek", "custom"}
