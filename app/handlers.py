
import html

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Я модератор комментариев.\n"
        "Добавьте меня админом в discussion group и выдайте право удалять сообщения.\n"
        "Команды: /chatid, /whereami, /help"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Что я делаю:\n"
        "— не трогаю автофорварды постов канала;\n"
        "— не трогаю комментарии внутри тредов;\n"
        "— удаляю сообщения, написанные просто в общий поток discussion group.\n\n"
        "Команды:\n"
        "/chatid — показать chat_id текущего чата\n"
        "/whereami — показать chat_id и признаки сообщения"
    )


async def chatid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    await update.effective_message.reply_text(
        f"chat_id: <code>{chat.id}</code>\n"
        f"title: {html.escape(chat.title or '')}\n"
        f"type: {chat.type}",
        parse_mode=ParseMode.HTML,
    )


async def whereami(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    chat = update.effective_chat
    await msg.reply_text(
        f"chat_id: <code>{chat.id}</code>\n"
        f"type: {chat.type}\n"
        f"message_thread_id: <code>{getattr(msg, 'message_thread_id', None)}</code>\n"
        f"is_automatic_forward: <code>{getattr(msg, 'is_automatic_forward', False)}</code>",
        parse_mode=ParseMode.HTML,
    )
