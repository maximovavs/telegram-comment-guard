import asyncio
import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.handlers import cmd_chatid, cmd_start, cmd_whereami
from app.moderation import build_moderation_handler
from app.settings import load_settings


def configure_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        level=level,
    )


def build_application():
    settings = load_settings()
    configure_logging(settings.log_level)
    logger = logging.getLogger("comment_guard")

    application = Application.builder().token(settings.bot_token).build()

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("chatid", cmd_chatid))
    application.add_handler(CommandHandler("whereami", cmd_whereami))
    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.UpdateType.EDITED_MESSAGE,
            build_moderation_handler(settings),
        )
    )

    logger.info(
        "Bot configured | config=%s | chats=%s",
        settings.config_path,
        list(settings.chats.keys()),
    )
    return application, settings, logger


async def run_polling() -> None:
    application, settings, logger = build_application()
    logger.info("Bot started in polling mode")
    await application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=False,
        close_loop=False,
    )


async def run_once() -> None:
    application, settings, logger = build_application()
    logger.info(
        "Bot started in oneshot mode | config=%s | chats=%s",
        settings.config_path,
        list(settings.chats.keys()),
    )

    await application.initialize()
    await application.start()
    try:
        updates = await application.bot.get_updates(timeout=0, allowed_updates=Update.ALL_TYPES)
        logger.info("Fetched %s pending updates", len(updates))

        for update in updates:
            try:
                await application.process_update(update)
            except Exception:
                logger.exception("Failed to process update_id=%s", update.update_id)

        if updates:
            last_update_id = updates[-1].update_id
            await application.bot.get_updates(
                offset=last_update_id + 1,
                timeout=0,
                allowed_updates=Update.ALL_TYPES,
            )
            logger.info("Confirmed updates through %s", last_update_id)
    finally:
        await application.stop()
        await application.shutdown()


def main() -> None:
    run_mode = os.getenv("RUN_MODE", "polling").strip().lower()
    if run_mode == "oneshot":
        asyncio.run(run_once())
    else:
        asyncio.run(run_polling())


if __name__ == "__main__":
    main()