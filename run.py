import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import get_settings
from app.db import Database
from app.handlers import admin, common, plans


async def main() -> None:
    settings = get_settings()
    db = Database(settings.database_path)
    db.initialize()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.include_router(admin.router)
    dp.include_router(plans.router)
    dp.include_router(common.router)

    await bot.delete_webhook(drop_pending_updates=False)
    logging.info("Bot started with long polling")
    try:
        await dp.start_polling(bot, db=db, settings=settings)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped.")
