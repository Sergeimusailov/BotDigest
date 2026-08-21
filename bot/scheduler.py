import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from . import config, db
from .digest import build_digest

logger = logging.getLogger(__name__)


async def send_morning_reminder(bot: Bot) -> None:
    await bot.send_message(
        config.CHAT_ID,
        "📝 Сегодня день сбора новостей! Напишите мне в личные сообщения, что у вас "
        "произошло за неделю — в пятницу утром соберу общий дайджест.",
    )


async def send_evening_reminder(bot: Bot) -> None:
    await bot.send_message(
        config.CHAT_ID,
        "⏰ Напоминание: если ещё не скинули новости мне в личку — самое время, "
        "завтра утром собираю дайджест!",
    )


async def send_digest(bot: Bot) -> None:
    entries = db.get_all_entries()
    text = build_digest(entries)

    if text is None:
        await bot.send_message(config.CHAT_ID, "На этой неделе никто не поделился новостями 🤷")
    else:
        message = f"📰 Дайджест недели\n\n{text}"
        try:
            await bot.send_message(config.CHAT_ID, message, parse_mode="Markdown")
        except TelegramBadRequest:
            logger.warning("Digest markdown failed to parse, sending as plain text")
            await bot.send_message(config.CHAT_ID, message)

    db.clear_entries()


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=config.TIMEZONE)
    scheduler.add_job(
        send_morning_reminder,
        CronTrigger(day_of_week="thu", hour=10, minute=0),
        args=[bot],
    )
    scheduler.add_job(
        send_evening_reminder,
        CronTrigger(day_of_week="thu", hour=19, minute=0),
        args=[bot],
    )
    scheduler.add_job(
        send_digest,
        CronTrigger(day_of_week="fri", hour=9, minute=0),
        args=[bot],
    )
    return scheduler
