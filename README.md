# Telegram Comment Guard — one repo, many bots

Это шаблон для ситуации, когда ты не хочешь плодить много репозиториев.

## Идея
Один репозиторий обслуживает несколько разных ботов.
Код у всех общий, а различаются только:
- `BOT_TOKEN`
- `CONFIG_PATH`

## Подходит для
- бота подруги;
- твоего отдельного бота для всех твоих каналов;
- других друзей позже, если понадобится.

## Структура

```text
telegram-comment-guard-one-repo-multi-bot/
├─ app/
│  ├─ __init__.py
│  ├─ handlers.py
│  ├─ main.py
│  ├─ moderation.py
│  └─ settings.py
├─ config/
│  ├─ README.md
│  ├─ friend_bot.example.json
│  └─ my_bot.example.json
├─ .env.example
├─ .gitignore
├─ README.md
└─ requirements.txt
```

## Что делать сначала

1. Создай один приватный GitHub-репозиторий.
2. Загрузи туда все файлы из этого архива.
3. Для первого деплоя создай `.env` на основе `.env.example`.
4. Выбери один пример конфига:
   - `config/friend_bot.example.json` → скопируй в `config/friend_bot.json`
   - `config/my_bot.example.json` → скопируй в `config/my_bot.json`
5. Заполни реальные `chat_id`.
6. Запусти бота локально или на Railway/Render/VPS.

## Важный принцип
Один деплой = один бот.

Но репозиторий может быть один.

То есть:
- деплой №1: бот подруги  
  `BOT_TOKEN=...`
  `CONFIG_PATH=config/friend_bot.json`

- деплой №2: твой бот  
  `BOT_TOKEN=...`
  `CONFIG_PATH=config/my_bot.json`

## Что загружать в GitHub

Загружай:
- папку `app/`
- папку `config/`
- `.env.example`
- `.gitignore`
- `requirements.txt`
- `README.md`

Не загружай:
- `.env` с реальными токенами
- при желании реальные `config/*.json`, если не хочешь хранить chat_id в репозитории

## Где токены
Токены не в файлах репозитория.
Они должны лежать:
- локально в `.env`
- или в secrets / environment variables на хостинге

## Какой бот где

### Бот подруги
- её красивый бот из BotFather
- её токен
- её discussion group
- её конфиг, например `config/friend_bot.json`

### Твой бот
- твой отдельный бот
- твой токен
- список твоих discussion group
- твой конфиг, например `config/my_bot.json`

## Пример `.env`

```env
BOT_TOKEN=123456:ABCDEF
CONFIG_PATH=config/friend_bot.json
OWNER_USER_IDS=123456789
DEFAULT_DELETE_NOTICE_AFTER_SECONDS=20
```

## Пример локального запуска

### Windows PowerShell
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.main
```

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

## Как подключить новый чат

1. Добавь нужного бота админом в discussion group.
2. Дай ему право удалять сообщения.
3. Отключи `Group Privacy` у бота в BotFather.
4. Напиши в этом чате `/chatid`.
5. Добавь полученный id в нужный json-конфиг.
6. Перезапусти деплой.

## Как подключить нового друга позже

У тебя есть два пути:

### Путь 1 — отдельный бот друга
- новый токен
- новый json-конфиг
- новый деплой из того же репозитория

### Путь 2 — твой общий бот
- тот же токен
- просто добавить ещё один chat_id в текущий конфиг

## Что лучше использовать сейчас

Для твоей текущей задачи:
- для подруги используй её бота;
- для себя потом поднимешь второй деплой из того же репозитория.

Это и красиво, и без хаоса.
