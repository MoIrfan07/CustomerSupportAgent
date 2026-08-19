from app.config import QWEN_LANGUAGE
from app.llm import qwen_model


messages = [
    (
        "system",
        (
            "You are a professional customer "
            "support assistant.\n\n"
            f"Always respond in {QWEN_LANGUAGE}."
        ),
    ),
    (
        "human",
        "Hello! Briefly introduce yourself.",
    ),
]


response = qwen_model.invoke(messages)


print("\n===== LANGCHAIN + QWEN =====\n")

print(response.content)