import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

DEFAULT_MODEL = "openai/gpt-oss-120b"


def get_llm(
    model: str | None = None,
    temperature: float = 0.0,
    timeout: float = 60.0,
    max_retries: int = 2,
) -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not api_key.strip():
        raise ValueError("GROQ_API_KEY is missing or empty. Set it in your .env file.")

    model_name = model or os.getenv("LLM_MODEL") or DEFAULT_MODEL

    return ChatGroq(
        model=model_name,
        temperature=temperature,
        timeout=timeout,
        max_retries=max_retries,
        api_key=api_key.strip(),
    )

