# Welcome Bot

A production-ready Telegram Welcome Bot built with **Aiogram 3.x** and **SQLite**.

## Features

- Sends a customisable welcome message when a new member joins a group
- Supports unlimited inline URL buttons attached to the welcome message
- Fully async — built on Aiogram 3.x and aiosqlite
- Multi-group support — each group has its own independent configuration
- Admin-only management commands
- HTML parse mode
- Structured logging
- Placeholder support in messages: `{name}`, `{chat}`

## Commands

| Command | Description |
|---|---|
| `/start` | Show help |
| `/set_welcome <text>` | Set the welcome message for this group |
| `/show_welcome` | Preview the current welcome message |
| `/del_welcome` | Delete the welcome message and all buttons |
| `/add_button <label> \| <url>` | Add an inline button to the welcome message |
| `/del_button <id>` | Remove a button by its ID |
| `/list_buttons` | List all configured buttons |

Management commands are restricted to group administrators and owners.

## Placeholders

Use these inside your welcome message text:

| Placeholder | Replaced with |
|---|---|
| `{name}` | The new member's full name |
| `{chat}` | The group's name |

Example:
```
/set_welcome Hello, {name}! Welcome to <b>{chat}</b> 🎉
```

## Setup

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your bot token:
   ```
   BOT_TOKEN=your_token_here
   ```
4. Run the bot:
   ```bash
   python bot.py
   ```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ | Telegram bot token from @BotFather |
| `LOG_LEVEL` | ❌ | Logging level (default: `INFO`) |

## Requirements

- Python 3.12+
- aiogram 3.20.0
- aiosqlite 0.22.1
- python-dotenv 1.2.2

## License

MIT
