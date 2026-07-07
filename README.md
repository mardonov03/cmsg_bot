# cmsg_bot (PurifyAi)

A Telegram moderation bot that automatically detects and removes banned content from group chats — including text patterns, stickers, audio, and NSFW images (via ML).

## Features

- **Custom ban list per group** — add any text, sticker, or audio to a blacklist; the bot deletes matching content automatically when it appears in the chat
- **Automatic NSFW image detection** — built-in ML model (TensorFlow + OpenNSFW2) scans photos in real time and removes explicit content without any manual list
- **Global ban list** — content flagged as NSFW is remembered, so identical images are blocked instantly across all groups without re-running the model
- **Admin permission checks** — the bot verifies it has the required admin rights in a group before activating, and prompts the user if permissions are missing
- **Multi-group support** — users can manage multiple groups from a single bot session and switch between them
- **Async architecture** — built on `aiogram` 3.x and `asyncpg` for non-blocking I/O under concurrent load

## How it works (user flow)

1. User starts the bot with `/start` and accepts the terms of use
2. Bot is added to a Telegram group with admin rights (mute/delete permissions required)
3. User selects which group to manage (if multiple)
4. User sends text, a sticker, or audio to the bot — it's added to that group's ban list
5. Any matching content posted in the group is deleted automatically
6. Photos are scanned automatically for NSFW content — no setup required

## Tech Stack

- **Python 3.12**, `aiogram 3.14` (Telegram Bot API)
- **PostgreSQL** + `asyncpg` (async driver, connection pooling)
- **TensorFlow 2.16** + `opennsfw2` (NSFW image classification)
- **FastAPI** (webhook endpoint)
- **Docker / docker-compose**

## Running locally

```bash
git clone https://github.com/mardonov03/cmsg_bot.git
cd cmsg_bot
docker compose up --build
```

The bot, database, and all dependencies start automatically — no manual setup required.

## Architecture

```
tgbot/
├── handlers/       # message and callback handlers
├── models/         # NSFW detection, business logic
├── database/       # PostgreSQL schema, queries
├── middlewares/     # aiogram middlewares
├── states/         # FSM states for multi-step flows
└── main.py         # entry point
```

## Notes

- NSFW sensitivity is adjustable per group via `/settings` (strict / medium / relaxed)
- Ban list matching works on exact content — text, `file_unique_id` for stickers/audio, and ML-based classification for images

## Feedback & Bug Reports

Found a bug or have an idea for improvement? Feel free to open an issue or reach out: **mardonovk233@gmail.com** or **https://t.me/mardonovk**
