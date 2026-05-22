
import logging

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


def main() -> None:
    settings = load_settings()

    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        level=logging.INFO,
    )
    logger = logging.getLogger("comment_guard")

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

    interesting_messages = (
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
    application.add_handler(
        MessageHandler(interesting_messages, build_moderation_handler(settings))
    )

    logger.info("Bot started | config=%s | chats=%s", settings.config_path, list(settings.chats.keys()))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
