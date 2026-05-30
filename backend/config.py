from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

AI_FEEDBACK_ENABLED = os.getenv("AI_FEEDBACK_ENABLED", "true").lower() == "true"
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"
GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-3-mini")
