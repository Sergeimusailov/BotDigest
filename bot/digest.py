def build_digest(entries: list[tuple[str, str]]) -> str | None:
    if not entries:
        return None

    by_person: dict[str, list[str]] = {}
    for name, text in entries:
        by_person.setdefault(name, []).append(text)

    blocks = []
    for name, texts in by_person.items():
        body = "\n".join(texts)
        blocks.append(f"*{name}*\n{body}")
    return "\n\n".join(blocks)
