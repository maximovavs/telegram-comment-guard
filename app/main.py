import asyncio
import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

import app.handlers as handlers_module
from app.moderation import build_moderation_handler
from app.settings import load_settings


def configure_logging(level_name: str) -> None:
    level = getattr(logging, str(level_name).upper(), logging.INFO)
    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        level=level,
    )


def _resolve_handler(*names):
    """
    Supports both naming styles:
    - start / chatid / whereami
    - cmd_start / cmd_chatid / cmd_whereami
    """
    for name in names:
        fn = getattr(handlers_module, name, None)
        if callable(fn):
            return fn
    return None


def build_application():
    settings = load_settings()

    log_level = getattr(settings, "log_level", "INFO")
    configure_logging(log_level)
    logger = logging.getLogger("comment_guard")

    bot_token = getattr(settings, "bot_token", None) or os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is empty")

    application = Application.builder().token(bot_token).build()

    start_handler = _resolve_handler("cmd_start", "start")
    chatid_handler = _resolve_handler("cmd_chatid", "chatid")
    whereami_handler = _resolve_handler("cmd_whereami", "whereami")

    if start_handler:
        application.add_handler(CommandHandler("start", start_handler))
    else:
        logger.warning("No /start handler found in app.handlers")

    if chatid_handler:
        application.add_handler(CommandHandler("chatid", chatid_handler))
    else:
        logger.warning("No /chatid handler found in app.handlers")

    if whereami_handler:
        application.add_handler(CommandHandler("whereami", whereami_handler))
    else:
        logger.warning("No /whereami handler found in app.handlers")

    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.UpdateType.EDITED_MESSAGE,
            build_moderation_handler(settings),
        )
    )

    config_path = getattr(settings, "config_path", os.getenv("CONFIG_PATH", ""))
    chats = list((getattr(settings, "chats", {}) or {}).keys())

    logger.info("Bot configured | config=%s | chats=%s", config_path, chats)
    return application, settings, logger


async def run_once() -> None:
    application, settings, logger = build_application()
    config_path = getattr(settings, "config_path", os.getenv("CONFIG_PATH", ""))
    chats = list((getattr(settings, "chats", {}) or {}).keys())

    logger.info(
        "Bot started in oneshot mode | config=%s | chats=%s",
        config_path,
        chats,
    )

    await application.initialize()
    await application.start()
    try:
        updates = await application.bot.get_updates(
            timeout=0,
            allowed_updates=Update.ALL_TYPES,
        )
        logger.info("Fetched %s pending updates", len(updates))

        for update in updates:
            msg = getattr(update, "effective_message", None)
            chat = getattr(update, "effective_chat", None)
            user = getattr(update, "effective_user", None)

            logger.info(
                "Update debug | update_id=%s | has_message=%s | chat_id=%s | chat_type=%s | user_id=%s | text=%r | caption=%r | thread_id=%s | is_auto_forward=%s | has_reply=%s",
                getattr(update, "update_id", None),
                msg is not None,
                getattr(chat, "id", None),
                getattr(chat, "type", None),
                getattr(user, "id", None),
                getattr(msg, "text", None) if msg else None,
                getattr(msg, "caption", None) if msg else None,
                getattr(msg, "message_thread_id", None) if msg else None,
                getattr(msg, "is_automatic_forward", False) if msg else None,
                getattr(msg, "reply_to_message", None) is not None if msg else None,
            )

            try:
                await application.process_update(update)
            except Exception:
                logger.exception(
                    "Failed to process update_id=%s",
                    getattr(update, "update_id", None),
                )

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
    run_mode = os.getenv("RUN_MODE", "oneshot").strip().lower()
    if run_mode == "oneshot":
        asyncio.run(run_once())
    else:
        raise RuntimeError("This build is prepared for RUN_MODE=oneshot only.")


if __name__ == "__main__":
    main()