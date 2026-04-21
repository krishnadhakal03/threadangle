import os
from typing import List, Dict, Any, Tuple


def _get_openai_v1_client(api_key: str):
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except Exception:
        return None


def _get_openai_legacy_module():
    try:
        import openai
        return openai
    except Exception:
        return None


def get_openai_client() -> Tuple[str, object]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return "missing", None

    client = _get_openai_v1_client(api_key)
    if client:
        return "v1", client

    legacy = _get_openai_legacy_module()
    if legacy:
        legacy.api_key = api_key
        return "legacy", legacy

    return "missing", None


def chat_complete(messages: List[Dict[str, str]], model: str, max_tokens: int = 800, temperature: float = 0.9) -> str:
    mode, client = get_openai_client()
    if mode == "missing" or client is None:
        raise RuntimeError("OPENAI_API_KEY is not set or OpenAI SDK not available.")

    if mode == "v1":
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return (response.choices[0].message.content or "").strip()

    response = client.ChatCompletion.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return (response.choices[0].message["content"] or "").strip()


def image_generate(prompt: str, model: str, size: str = "1024x1024") -> str:
    mode, client = get_openai_client()
    if mode == "missing" or client is None:
        raise RuntimeError("OPENAI_API_KEY is not set or OpenAI SDK not available.")

    if mode == "v1":
        response = client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            response_format="b64_json",
        )
        return response.data[0].b64_json

    response = client.Image.create(
        prompt=prompt,
        size=size,
        response_format="b64_json",
    )
    return response["data"][0]["b64_json"]
