import asyncio
import logging

from aiogram import Bot, Dispatcher

from . import config, db
from .handlers import router
from .scheduler import setup_scheduler


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    db.init_db()

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    scheduler = setup_scheduler(bot)
    scheduler.start()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
