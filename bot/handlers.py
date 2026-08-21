from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from . import db

router = Router()


@router.message(CommandStart(), F.chat.type == "private")
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет! Я собираю новости для еженедельного дайджеста чата.\n\n"
        "Просто напиши мне сюда, что у тебя нового — можно несколькими сообщениями, "
        "я всё соберу. Раз в неделю по утрам в пятницу я формирую общий дайджест "
        "и отправляю его в чат — никто не увидит твои сообщения до этого момента."
    )


@router.message(F.chat.type == "private", F.text, ~F.text.startswith("/"))
async def collect_news(message: Message) -> None:
    name = message.from_user.full_name
    db.add_entry(message.from_user.id, name, message.text)
    await message.answer("Записал ✍️ Можешь дописать ещё или просто жди дайджест в пятницу.")
