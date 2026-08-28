import os


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


BOT_TOKEN = _required("BOT_TOKEN")
CHAT_ID = int(_required("CHAT_ID"))

TIMEZONE = os.environ.get("TIMEZONE", "Europe/Moscow")
DB_PATH = os.environ.get("DB_PATH", "botdigest.db")
