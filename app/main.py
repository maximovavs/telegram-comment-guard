import asyncio
import logging
import os

from telegram import Update
from telegram.ext import (
    AIORateLimiter,
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.handlers import chatid, help_cmd, start, whereami
from app.moderation import build_moderation_handler
from app.settings import load_settings


INTERESTING_MESSAGES = (
    filters.TEXT
    | filters.PHOTO
    | filters.VIDEO
    | filters.Document.ALL
    | filters.VOICE
    | filters.AUDIO
    | filters.Sticker.ALL
    | filters.CONTACT
    | filters.LOCATION
)


def build_application(settings):
    application = (
        Application.builder()
        .token(settings.bot_token)
        .rate_limiter(AIORateLimiter())
        .build()
    )

    application.bot._application = application  # type: ignore[attr-defined]

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("chatid", chatid))
    application.add_handler(CommandHandler("whereami", whereami))
    application.add_handler(
        MessageHandler(INTERESTING_MESSAGES, build_moderation_handler(settings))
    )
    return application


async def run_once() -> None:
    settings = load_settings()
    logger = logging.getLogger("comment_guard")
    application = build_application(settings)

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

        max_update_id = None
        for update in updates:
            await application.process_update(update)
            max_update_id = update.update_id

        if max_update_id is not None:
            # Подтверждаем все обновления до max_update_id включительно,
            # чтобы на следующем запуске они не пришли повторно.
            await application.bot.get_updates(offset=max_update_id + 1, timeout=0)
            logger.info("Confirmed updates through %s", max_update_id)
    finally:
        await application.stop()
        await application.shutdown()



def run_polling() -> None:
    settings = load_settings()
    logger = logging.getLogger("comment_guard")
    application = build_application(settings)

    logger.info(
        "Bot started in polling mode | config=%s | chats=%s",
        settings.config_path,
        list(settings.chats.keys()),
    )
    application.run_polling(allowed_updates=Update.ALL_TYPES)



def main() -> None:
    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    )

    run_mode = os.getenv("RUN_MODE", "polling").strip().lower()
    if run_mode == "oneshot":
        asyncio.run(run_once())
    else:
        run_polling()


if __name__ == "__main__":
    main()
