# Welcome Bot

A production-ready Telegram Welcome Bot built with **Aiogram 3.x** and **PostgreSQL**.

## Features

- Sends a customisable welcome message when a new member joins a group
- Supports unlimited inline URL buttons attached to the welcome message
- Fully async — built on Aiogram 3.x and asyncpg
- Multi-group support — each group has its own independent configuration
- Admin-only management commands
- HTML parse mode with placeholder support
- Broadcast system for reaching all known chats
- Channel tracking (informational)
- Structured logging
- Railway-ready deployment

## Commands

| Command | Description |
|---|---|
| `/start` | Show main menu |
| `/set_welcome <text>` | Set the welcome message for this group |
| `/show_welcome` | Preview the current welcome message |
| `/del_welcome` | Delete the welcome message and all buttons |
| `/add_button <label> \| <url>` | Add an inline button to the welcome message |
| `/del_button <id>` | Remove a button by its ID |
| `/list_buttons` | List all configured buttons |
| `/add_channel` | Register a channel (reply to forwarded msg, or pass @username / ID) |
| `/del_channel <channel_id>` | Remove a registered channel |
| `/list_channels` | List all registered channels |
| `/broadcast` | Send a message to all known chats (super-admin only) |
| `/stats` | Show bot statistics |
| `/cancel` | Cancel the current operation |

Management commands are restricted to group administrators and owners.  
`/broadcast` is restricted to user IDs listed in `BROADCAST_ADMIN_IDS`.

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

### Local development

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in the required values:
   ```bash
   cp .env.example .env
   ```
4. Run the bot:
   ```bash
   python bot.py
   ```

### Railway deployment

1. Create a new Railway project and link this repository.
2. Add the **PostgreSQL** plugin — Railway injects `DATABASE_URL` automatically.
3. Set `BOT_TOKEN` in the Railway environment variables dashboard.
4. Set `BROADCAST_ADMIN_IDS` (optional) to your Telegram user ID(s).
5. Deploy — Railway uses `railway.toml` to build and start the bot.

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `BOT_TOKEN` | ✅ | — | Telegram bot token from @BotFather |
| `DATABASE_URL` | ✅ | — | PostgreSQL connection string (injected by Railway) |
| `BROADCAST_ADMIN_IDS` | ❌ | *(empty)* | Comma-separated Telegram user IDs for `/broadcast` |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `TZ` | ❌ | `UTC` | Timezone string for log timestamps |
| `MAX_CONCURRENT_TASKS` | ❌ | `2` | Max concurrent broadcast tasks |
| `START_FROM_LATEST` | ❌ | `true` | Drop updates queued while the bot was offline |

See `.env.example` for a fully commented template.

## Requirements

- Python 3.12+
- aiogram 3.20.0
- asyncpg 0.30.0
- python-dotenv 1.2.2

## Database

The bot uses **PostgreSQL** exclusively. On first startup it creates four tables:

| Table | Purpose |
|---|---|
| `welcome_messages` | Stores welcome text per chat |
| `buttons` | Inline buttons linked to welcome messages |
| `channels` | Registered channels (informational) |
| `known_chats` | Broadcast target tracking |

No migrations are required — tables are created with `CREATE TABLE IF NOT EXISTS`.

## License

MIT
