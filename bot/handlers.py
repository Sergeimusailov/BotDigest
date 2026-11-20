import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import BaseFilter, Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from . import config, db

logger = logging.getLogger(__name__)

router = Router()


async def is_chat_member(bot: Bot, user_id: int) -> bool:
    """Проверяет, состоит ли пользователь в групповом чате дайджеста."""
    try:
        member = await bot.get_chat_member(config.CHAT_ID, user_id)
    except TelegramAPIError as exc:
        logger.warning("Не удалось проверить участника %s: %s", user_id, exc)
        return False

    if member.status in (
        ChatMemberStatus.CREATOR,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.MEMBER,
    ):
        return True
    # «Ограниченный» участник всё ещё в чате, если is_member=True
    return member.status == ChatMemberStatus.RESTRICTED and getattr(member, "is_member", False)


class IsNotChatMember(BaseFilter):
    """Срабатывает для личных сообщений от тех, кого нет в групповом чате."""

    async def __call__(self, message: Message, bot: Bot) -> bool:
        if message.from_user is None:
            return True
        return not await is_chat_member(bot, message.from_user.id)


# Этот обработчик стоит первым: любое личное сообщение от постороннего
# перехватывается здесь и дальше не идёт — ни команды, ни сохранение новостей.
# Бот посторонним ничего не отвечает: для них он выглядит неработающим.
@router.message(F.chat.type == "private", IsNotChatMember())
async def ignore_stranger(message: Message) -> None:
    logger.info(
        "Проигнорировано сообщение от постороннего: id=%s, name=%s",
        message.from_user.id if message.from_user else None,
        message.from_user.full_name if message.from_user else None,
    )


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
