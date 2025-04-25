"""Configs variables related to llms and ml logic"""

LLM_CONFIGS = {
    "gemini-1.5-flash": {
        "model": "gemini-1.5-flash-002",
        "max_output_tokens": 1024,
        "temperature": 0.0,
    },
    "gemini-1.5-pro": {
        "model": "gemini-1.5-pro-002",
        "max_output_tokens": 1024,
        "temperature": 1.0,
    },
    "gemini-2.0-flash": {
        "model": "gemini-2.0-flash-001",
        "max_output_tokens": 1024,
        "temperature": 0.0,
    }
}
