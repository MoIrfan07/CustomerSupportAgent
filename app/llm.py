from langchain_openai import ChatOpenAI

from app.config import (
    QWEN_API_KEY,
    QWEN_COMPATIBLE_BASE_URL,
    QWEN_MODEL,
)


def create_qwen_model() -> ChatOpenAI:
    """
    Create the LangChain chat model
    backed by QwenCloud.
    """

    return ChatOpenAI(
        model=QWEN_MODEL,
        api_key=QWEN_API_KEY,
        base_url=QWEN_COMPATIBLE_BASE_URL,
        temperature=0.2,
        max_retries=2,
        timeout=60,
    )


qwen_model = create_qwen_model()
