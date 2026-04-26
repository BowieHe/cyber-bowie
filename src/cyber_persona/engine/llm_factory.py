"""Unified factory for creating LLM instances."""

from langchain_openai import ChatOpenAI
from cyber_persona.config import get_settings


def _get_attr(obj, *names):
    """Try multiple attribute names, return first non-None value."""
    for name in names:
        val = getattr(obj, name, None)
        if val is not None:
            return val
    return None


def get_llm(
    llm: ChatOpenAI | None = None,
    *,
    light: bool = False,
    temperature: float | None = None,
    model: str | None = None,
    base_url: str | None = None,
    model_kwargs: dict | None = None,
    extra_body: dict | None = None,
) -> ChatOpenAI:
    """Get an existing LLM or create a new one from settings.

    Override rules: if a parameter is passed (including empty dict {}),
    it replaces the base value entirely.  If None, the base value is kept.

    When ``llm`` is provided and no overrides are given, it is returned
    as-is for performance.  When overrides are present, a new instance is
    built by copying the base parameters and applying the overrides.
    """
    has_override = any(
        p is not None for p in (temperature, model, base_url, model_kwargs, extra_body)
    )

    # Fast path: reuse existing instance when nothing needs to change.
    if llm is not None and not has_override:
        return llm

    # Determine base parameters.
    if llm is not None:
        base_model = _get_attr(llm, "model", "model_name")
        base_api_key = _get_attr(llm, "openai_api_key", "api_key")
        base_base_url = _get_attr(llm, "openai_api_base", "base_url")
        base_temperature = _get_attr(llm, "temperature")
        base_model_kwargs = _get_attr(llm, "model_kwargs") or {}
        base_extra_body = _get_attr(llm, "extra_body") or {}
    else:
        settings = get_settings()
        config = settings.llm_light if light else settings.llm
        base_model = config.model
        base_api_key = config.api_key
        base_base_url = config.base_url
        base_temperature = config.temperature
        base_model_kwargs = config.model_kwargs
        base_extra_body = config.extra_body

    return ChatOpenAI(
        model=model if model is not None else base_model,
        api_key=base_api_key,
        base_url=base_url if base_url is not None else base_base_url,
        temperature=temperature if temperature is not None else base_temperature,
        model_kwargs=model_kwargs if model_kwargs is not None else base_model_kwargs.copy(),
        extra_body=extra_body if extra_body is not None else base_extra_body.copy(),
        max_retries=5,
    )
