import os

from dotenv import load_dotenv


load_dotenv()


# ============================================
# QWEN CONFIGURATION
# ============================================

QWEN_MODEL = "qwen-flash-character"

QWEN_LANGUAGE = "English"


# Native DashScope API
QWEN_BASE_URL = (
    "https://dashscope-intl.aliyuncs.com/api/v1"
)


# OpenAI-compatible API
QWEN_COMPATIBLE_BASE_URL = (
    "https://dashscope-intl.aliyuncs.com/"
    "compatible-mode/v1"
)


# ============================================
# API KEY
# ============================================

QWEN_API_KEY = os.getenv(
    "DASHSCOPE_API_KEY"
)


if not QWEN_API_KEY:
    raise RuntimeError(
        "DASHSCOPE_API_KEY was not found."
    )