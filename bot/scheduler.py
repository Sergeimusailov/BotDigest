import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, EVENT_JOB_MISSED
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from . import config, db
from .digest import build_digest

logger = logging.getLogger(__name__)


async def _write_news_keyboard(bot: Bot) -> InlineKeyboardMarkup:
    me = await bot.get_me()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Написать новости", url=f"https://t.me/{me.username}")]
        ]
    )


async def send_morning_reminder(bot: Bot) -> None:
    logger.info("Running send_morning_reminder")
    await bot.send_message(
        config.CHAT_ID,
        "📝 Сегодня день сбора новостей! Напишите мне в личные сообщения, что у вас "
        "произошло за неделю — в пятницу утром соберу общий дайджест.",
        reply_markup=await _write_news_keyboard(bot),
    )
    logger.info("send_morning_reminder sent")


async def send_evening_reminder(bot: Bot) -> None:
    logger.info("Running send_evening_reminder")
    await bot.send_message(
        config.CHAT_ID,
        "⏰ Напоминание: если ещё не скинули новости мне в личку — самое время, "
        "завтра утром собираю дайджест!",
        reply_markup=await _write_news_keyboard(bot),
    )
    logger.info("send_evening_reminder sent")


async def send_digest(bot: Bot) -> None:
    logger.info("Running send_digest")
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
    logger.info("send_digest sent")


def _log_job_event(event) -> None:
    if event.code == EVENT_JOB_MISSED:
        logger.error("Job %s MISSED its scheduled run time %s", event.job_id, event.scheduled_run_time)
    elif event.code == EVENT_JOB_ERROR:
        logger.error("Job %s raised an exception: %s", event.job_id, event.exception)
    elif event.code == EVENT_JOB_EXECUTED:
        logger.info("Job %s executed successfully", event.job_id)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=config.TIMEZONE)
    # CronTrigger does NOT inherit the scheduler's timezone — each trigger falls back
    # to the host's local timezone unless given one explicitly, so it must be passed here too.
    scheduler.add_job(
        send_morning_reminder,
        CronTrigger(day_of_week="thu", hour=12, minute=0, timezone=config.TIMEZONE),
        args=[bot],
        id="send_morning_reminder",
    )
    scheduler.add_job(
        send_evening_reminder,
        CronTrigger(day_of_week="thu", hour=17, minute=0, timezone=config.TIMEZONE),
        args=[bot],
        id="send_evening_reminder",
    )
    scheduler.add_job(
        send_digest,
        CronTrigger(day_of_week="fri", hour=9, minute=0, timezone=config.TIMEZONE),
        args=[bot],
        id="send_digest",
    )
    scheduler.add_listener(
        _log_job_event, EVENT_JOB_ERROR | EVENT_JOB_MISSED | EVENT_JOB_EXECUTED
    )
    return scheduler
