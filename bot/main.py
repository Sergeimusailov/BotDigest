import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from . import config, db
from .handlers import router
from .scheduler import setup_scheduler


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    db.init_db()

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await bot.set_my_commands(
        [
            BotCommand(command="preview", description="Что попадёт в дайджест"),
            BotCommand(command="undo", description="Удалить последнее сообщение"),
            BotCommand(command="clear", description="Удалить все свои сообщения"),
        ]
    )

    scheduler = setup_scheduler(bot)
    scheduler.start()
    for job in scheduler.get_jobs():
        logging.info("Scheduled job %s — next run at %s", job.id, job.next_run_time)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
