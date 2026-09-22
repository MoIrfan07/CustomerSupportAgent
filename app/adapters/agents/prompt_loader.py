from __future__ import annotations

from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_core.prompts import ChatPromptTemplate


def render_prompt_file(
    prompt_path: Path,
    *,
    username: str,
    user_role: str,
    customer_id: str | None,
    qwen_language: str,
) -> str:
    """Load a Markdown prompt with LangChain and render its runtime values."""
    if not prompt_path.is_file():
        raise FileNotFoundError(f"Prompt file was not found: {prompt_path}")

    documents = TextLoader(str(prompt_path), encoding="utf-8").load()
    prompt_text = "\n".join(document.page_content for document in documents)
    prompt = ChatPromptTemplate.from_messages([("system", prompt_text)])
    rendered = prompt.invoke(
        {
            "USERNAME": username,
            "USER_ROLE": user_role,
            "CUSTOMER_ID": customer_id or "",
            "QWEN_LANGUAGE": qwen_language,
        }
    )

    content = rendered.messages[0].content
    if not isinstance(content, str):
        raise TypeError(f"Prompt content must be text: {prompt_path}")
    return content
