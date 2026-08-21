from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from . import db

router = Router()


@router.message(CommandStart(), F.chat.type == "private")
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет! Я собираю новости для еженедельного дайджеста чата.\n\n"
        "Просто напиши мне сюда, что у тебя нового — можно несколькими сообщениями, "
        "я всё соберу. Раз в неделю по утрам в пятницу я формирую общий дайджест "
        "и отправляю его в чат — никто не увидит твои сообщения до этого момента.\n\n"
        "Команды:\n"
        "/preview — что сейчас сохранено и попадёт в дайджест\n"
        "/undo — удалить последнее сообщение\n"
        "/clear — удалить все свои сообщения за неделю"
    )


@router.message(Command("preview"), F.chat.type == "private")
async def cmd_preview(message: Message) -> None:
    entries = db.get_entries_for_user(message.from_user.id)
    if not entries:
        await message.answer("Пока нет сохранённых сообщений на этой неделе.")
        return
    numbered = "\n".join(f"{i}. {text}" for i, text in enumerate(entries, start=1))
    await message.answer(f"Сейчас сохранено (попадёт в дайджест):\n\n{numbered}")


@router.message(Command("undo"), F.chat.type == "private")
async def cmd_undo(message: Message) -> None:
    if db.delete_last_for_user(message.from_user.id):
        await message.answer("Последнее сообщение удалено ✍️ Можешь написать новое.")
    else:
        await message.answer("Нечего отменять — у тебя нет сохранённых сообщений.")


@router.message(Command("clear"), F.chat.type == "private")
async def cmd_clear(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да, удалить всё", callback_data="clear_confirm"),
                InlineKeyboardButton(text="Отмена", callback_data="clear_cancel"),
            ]
        ]
    )
    await message.answer(
        "Точно удалить все твои сохранённые сообщения за эту неделю? "
        "Это затронет только твои записи, у остальных ничего не удалится.",
        reply_markup=keyboard,
    )


@router.callback_query(F.data == "clear_confirm")
async def cb_clear_confirm(callback: CallbackQuery) -> None:
    deleted = db.delete_all_for_user(callback.from_user.id)
    if deleted:
        await callback.message.edit_text(
            f"Удалено сообщений: {deleted}. Можешь начать писать заново."
        )
    else:
        await callback.message.edit_text("У тебя и так не было сохранённых сообщений.")
    await callback.answer()


@router.callback_query(F.data == "clear_cancel")
async def cb_clear_cancel(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Отменено, ничего не удалено.")
    await callback.answer()


@router.message(F.chat.type == "private", F.text, ~F.text.startswith("/"))
async def collect_news(message: Message) -> None:
    name = message.from_user.full_name
    db.add_entry(message.from_user.id, name, message.text)
    await message.answer("Записал ✍️ Можешь дописать ещё или просто жди дайджест в пятницу.")
