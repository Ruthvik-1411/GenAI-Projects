"""Config file LLM related config values"""

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
    "gemini-2.0-flash-lite": {
        "model": "gemini-2.0-flash-lite-preview-02-05",
        "max_output_tokens": 1024,
        "temperature": 0.0,
    }
}

MODELS = list(LLM_CONFIGS.keys())

ALLOWED_FILE_TYPES = ["png", "jpg", "jpeg", "mp4", "pdf"]
