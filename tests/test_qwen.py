import dashscope

from dashscope import Generation

from app.config import (
    QWEN_API_KEY,
    QWEN_BASE_URL,
    QWEN_MODEL,
)


# ============================================
# CONFIGURE QWEN
# ============================================

dashscope.base_http_api_url = QWEN_BASE_URL


# ============================================
# MESSAGES
# ============================================

messages = [

    {
        "role": "system",

        "content": (
            "You are a friendly customer "
            "support assistant. "
            "Be concise, professional "
            "and helpful."
        ),
    },

    {
        "role": "user",

        "content": (
            "Hello! What can you help "
            "me with?"
        ),
    },

]


# ============================================
# CALL QWEN
# ============================================

response = Generation.call(

    api_key=QWEN_API_KEY,

    model=QWEN_MODEL,

    messages=messages,

    result_format="message",

)


# ============================================
# ERROR HANDLING
# ============================================

if response.status_code != 200:

    raise RuntimeError(

        f"Qwen API error: "
        f"{response.code} - "
        f"{response.message}"

    )


# ============================================
# OUTPUT
# ============================================

print(
    "\n===== QWEN RESPONSE =====\n"
)


print(

    response.output
    .choices[0]
    .message
    .content

)