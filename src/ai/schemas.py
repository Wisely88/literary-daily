EVALUATION_SCHEMA = {
    "type": "object",
    "properties": {
        "literary_quality": {"type": "integer"},
        "depth": {"type": "integer"},
        "language_quality": {"type": "integer"},
        "read_aloud_quality": {"type": "integer"},
        "emotional_value": {"type": "integer"},
        "excerpt_quality": {"type": "integer"},
        "timelessness": {"type": "integer"},
        "reason": {"type": "string"},
    },
    "required": ["literary_quality", "depth", "language_quality", "read_aloud_quality", "emotional_value", "excerpt_quality", "timelessness", "reason"],
}

ARTICLE_SCHEMA = {
    "type": "object",
    "properties": {
        "recommendation": {"type": "string"},
        "introduction": {"type": "string"},
        "excerpt": {"type": "string"},
        "afterword": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "tts_text": {"type": "string"},
    },
    "required": ["recommendation", "introduction", "excerpt", "afterword", "tags", "tts_text"],
}
