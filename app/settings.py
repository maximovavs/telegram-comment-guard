
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent


@dataclass
class ChatRule:
    chat_id: int
    title: str = ""
    enabled: bool = True
    notify_mode: str = "group"  # group | dm | dm_then_group | none
    delete_notice_after_seconds: int = 20
    warning_template: str = (
        "Комментарий удалён, потому что он не был привязан ни к одному посту.\n\n"
        "<b>Ваш текст:</b>\n{text}"
    )
    exempt_user_ids: list[int] = field(default_factory=list)


@dataclass
class Settings:
    bot_token: str
    owner_user_ids: set[int]
    config_path: Path
    default_warning_template: str
    default_delete_notice_after_seconds: int
    chats: dict[int, ChatRule]


def parse_id_list(raw: str | None) -> set[int]:
    if not raw:
        return set()
    result: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        result.add(int(part))
    return result


def _resolve_config_path(raw: str | None) -> Path:
    if not raw:
        return ROOT_DIR / "config" / "chats.json"
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path


def load_settings() -> Settings:
    load_dotenv(ROOT_DIR / ".env")

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is empty. Put it in .env or hosting secrets.")

    config_path = _resolve_config_path(os.getenv("CONFIG_PATH"))
    if not config_path.exists():
        raise RuntimeError(
            f"Missing config file: {config_path}. "
            f"Create it from one of the examples in config/."
        )

    default_warning_template = os.getenv(
        "DEFAULT_WARNING_TEMPLATE",
        "Комментарий удалён, потому что он не был привязан ни к одному посту.\n\n"
        "<b>Ваш текст:</b>\n{text}",
    )
    default_delete_notice_after_seconds = int(
        os.getenv("DEFAULT_DELETE_NOTICE_AFTER_SECONDS", "20")
    )
    owner_user_ids = parse_id_list(os.getenv("OWNER_USER_IDS"))

    with config_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    chats: dict[int, ChatRule] = {}
    for item in raw.get("chats", []):
        chat_id = int(item["chat_id"])
        chats[chat_id] = ChatRule(
            chat_id=chat_id,
            title=item.get("title", ""),
            enabled=bool(item.get("enabled", True)),
            notify_mode=item.get("notify_mode", "group"),
            delete_notice_after_seconds=int(
                item.get(
                    "delete_notice_after_seconds",
                    default_delete_notice_after_seconds,
                )
            ),
            warning_template=item.get("warning_template", default_warning_template),
            exempt_user_ids=[int(x) for x in item.get("exempt_user_ids", [])],
        )

    return Settings(
        bot_token=bot_token,
        owner_user_ids=owner_user_ids,
        config_path=config_path,
        default_warning_template=default_warning_template,
        default_delete_notice_after_seconds=default_delete_notice_after_seconds,
        chats=chats,
    )
