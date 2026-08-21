import os


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


BOT_TOKEN = _required("BOT_TOKEN")
CHAT_ID = int(_required("CHAT_ID"))
ANTHROPIC_API_KEY = _required("ANTHROPIC_API_KEY")

TIMEZONE = os.environ.get("TIMEZONE", "Europe/Moscow")
DB_PATH = os.environ.get("DB_PATH", "botdigest.db")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
