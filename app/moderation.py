
import html
import logging
from typing import Any

from telegram import Update
from telegram.constants import ChatType, ParseMode
from telegram.error import Forbidden, TelegramError
from telegram.ext import ContextTypes

from app.settings import ChatRule, Settings

logger = logging.getLogger("comment_guard")


def is_allowed_message(message: Any) -> bool:
    if getattr(message, "is_automatic_forward", False):
        return True

    if getattr(message, "message_thread_id", None) is not None:
        return True

    if getattr(message, "reply_to_message", None) is not None:
        return True

    text = message.text or message.caption or ""
    if text.startswith("/"):
        return True

    return False


def render_removed_message(update: Update, rule: ChatRule, settings: Settings) -> str:
    message = update.effective_message
    user = update.effective_user

    raw_text = message.text or message.caption or "[сообщение без текста]"
    safe_text = html.escape(raw_text)
    name = html.escape(user.full_name if user else "Пользователь")
    mention = f"<b>{name}</b>"
    chat_title = html.escape(update.effective_chat.title or "")
    template = rule.warning_template or settings.default_warning_template
    return template.format(
        text=safe_text,
        user_name=name,
        mention=mention,
        chat_title=chat_title,
    )


async def delete_message_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.job.data or {}
    chat_id = data.get("chat_id")
    message_id = data.get("message_id")
    if not chat_id or not message_id:
        return
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramError:
        pass


async def notify_user_or_group(update: Update, rule: ChatRule, formatted_html: str) -> None:
    message = update.effective_message
    user = update.effective_user

    async def send_group_notice() -> None:
        sent = await message.get_bot().send_message(
            chat_id=message.chat_id,
            text=formatted_html,
            parse_mode=ParseMode.HTML,
        )
        if rule.delete_notice_after_seconds > 0:
            bot = update.get_bot()
            app = getattr(bot, "_application", None)
            if app and app.job_queue:
                app.job_queue.run_once(
                    delete_message_job,
                    when=rule.delete_notice_after_seconds,
                    data={"chat_id": sent.chat_id, "message_id": sent.message_id},
                )

    if rule.notify_mode == "none":
        return

    if rule.notify_mode in {"dm", "dm_then_group"} and user:
        try:
            await message.get_bot().send_message(
                chat_id=user.id,
                text=formatted_html,
                parse_mode=ParseMode.HTML,
            )
            return
        except Forbidden:
            if rule.notify_mode == "dm":
                return
        except TelegramError:
            if rule.notify_mode == "dm":
                return

    if rule.notify_mode in {"group", "dm_then_group"}:
        await send_group_notice()


def build_moderation_handler(settings: Settings):
    async def moderate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.effective_message
        chat = update.effective_chat
        user = update.effective_user

        if not message or not chat or chat.type != ChatType.SUPERGROUP:
            return

        rule = settings.chats.get(chat.id)
        if not rule or not rule.enabled:
            return

        if user and (user.id in settings.owner_user_ids or user.id in rule.exempt_user_ids):
            return

        if is_allowed_message(message):
            return

        formatted_html = render_removed_message(update, rule, settings)

        try:
            await message.delete()
        except TelegramError as exc:
            logger.warning("Failed to delete message in chat %s: %s", chat.id, exc)
            return

        logger.info(
            "Deleted off-thread message | chat_id=%s | user_id=%s | message_id=%s",
            chat.id,
            user.id if user else None,
            message.message_id,
        )

        try:
            await notify_user_or_group(update, rule, formatted_html)
        except TelegramError as exc:
            logger.warning("Failed to notify after deletion: %s", exc)

    return moderate
