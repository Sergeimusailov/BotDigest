from anthropic import Anthropic

from . import config

_client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

_PROMPT_TEMPLATE = """Ниже — новости от участников чата за неделю. Один человек мог прислать несколько сообщений.

Сделай из этого дайджест: для каждого человека — короткий связный абзац (2-4 предложения) по его сообщениям. \
Сохраняй факты и смысл, ничего не выдумывай и не добавляй лишнего. Без общего вступления и заключения.

Формат вывода строго такой (используй одинарные звёздочки для имени, это Telegram Markdown):
*Имя*
текст абзаца

*Имя2*
текст абзаца

Сырые сообщения:
{raw}
"""


def _format_raw(entries: list[tuple[str, str]]) -> str:
    by_person: dict[str, list[str]] = {}
    for name, text in entries:
        by_person.setdefault(name, []).append(text)

    blocks = []
    for name, texts in by_person.items():
        joined = "\n".join(f"- {t}" for t in texts)
        blocks.append(f"{name}:\n{joined}")
    return "\n\n".join(blocks)


def build_digest(entries: list[tuple[str, str]]) -> str | None:
    if not entries:
        return None

    prompt = _PROMPT_TEMPLATE.format(raw=_format_raw(entries))

    response = _client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
