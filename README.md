# Welcome Bot 🤖

A production-ready Telegram Welcome Bot built with **Aiogram 3.x** and **PostgreSQL** deployed on **Railway**.

## ✨ Features

- 👋 Sends customizable welcome messages when new members join a group
- 🔗 Unlimited inline URL buttons attached to welcome messages
- ⚡ Fully async — built on Aiogram 3.x and asyncpg
- 🌍 Multi-group support — each group has independent configuration
- 🔐 Admin-only management commands
- 📝 HTML parse mode for rich text formatting
- 📊 Structured logging and statistics
- {name}, {chat} placeholder support in messages

## 🚫 What This Bot Does NOT Do

- ✅ Does NOT enforce channel subscriptions or force-subscribe
- ✅ Does NOT block users based on membership
- ✅ Channel registration is for administrative tracking only
- ✅ All users can interact with the bot freely

## 📋 Commands

### General

| Command | Description |
|---------|-------------|
| `/start` | Show main menu and features |

### Welcome System (Admin Only)

| Command | Description | Example |
|---------|-------------|----------|
| `/set_welcome <text>` | Set welcome message for this group | `/set_welcome Welcome, {name}! 🎉` |
| `/show_welcome` | Preview the current welcome message | — |
| `/del_welcome` | Delete welcome message and all buttons | — |

### Buttons (Admin Only)

| Command | Description | Example |
|---------|-------------|----------|
| `/add_button <label> \| <url>` | Add inline button to welcome | `/add_button Visit us \| https://example.com` |
| `/del_button <id>` | Remove button by ID | `/del_button 5` |
| `/list_buttons` | Show all configured buttons | — |

### Channel Management (Admin Only)

| Command | Description | Note |
|---------|-------------|-------|
| `/add_channel` | Register a channel (informational) | No subscription enforcement |
| `/del_channel <id>` | Remove registered channel | — |
| `/list_channels` | List all registered channels | — |

### Admin Tools

| Command | Description |
|---------|-------------|
| `/stats` | Show bot statistics and reach |
| `/broadcast` | Send message to all known chats (super-admin only) |
| `/cancel` | Cancel current operation |

## 🔖 Placeholders

Use these inside welcome messages:

| Placeholder | Replaced With |
|-------------|----------------|
| `{name}` | New member's full name |
| `{chat}` | Group name |

**Example:**
```
/set_welcome Hello {name}! Welcome to <b>{chat}</b> 🎉
```

## 🚀 Deployment Guide

### On Railway

1. **Create a new Railway project**
2. **Add PostgreSQL plugin:**
   - In Railway dashboard → Plugins → PostgreSQL
   - Attach to this service
3. **Set environment variables:**
   - `BOT_TOKEN`: Your Telegram bot token (from @BotFather)
   - `BROADCAST_ADMIN_IDS` (optional): Comma-separated user IDs for /broadcast
   - `LOG_LEVEL` (optional): DEBUG, INFO, WARNING (default: INFO)
4. **Deploy:**
   - Connect GitHub repository
   - Railway auto-deploys on push to `main`

### Railway will automatically:
- ✅ Inject `DATABASE_URL` from PostgreSQL plugin
- ✅ Run build: `pip install -r requirements.txt`
- ✅ Start bot: `python bot.py`

## 🔧 Environment Variables

### Required

- **BOT_TOKEN** — Telegram bot token from @BotFather
  - Format: `1234567890:ABCDEFGHIJKLMNOPQRSTUVWxyz`
  - 🔒 Keep this secret!

- **DATABASE_URL** — PostgreSQL connection (auto-injected by Railway)
  - Format: `postgresql://user:pass@host:port/db`
  - 🔒 Keep this secret!

### Optional

- **BROADCAST_ADMIN_IDS** — Users allowed to use `/broadcast`
  - Format: `123456789,987654321`
  - Default: Empty (no one can broadcast)

- **LOG_LEVEL** — Logging verbosity
  - Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
  - Default: `INFO`

- **MAX_CONCURRENT_TASKS** — Max async tasks
  - Default: `2`
  - Adjust based on Railway resources

- **START_FROM_LATEST** — Ignore pending updates on restart
  - Options: `true` (clean start), `false` (catchup mode)
  - Default: `true`

- **TZ** — Timezone for logs
  - Examples: `UTC`, `Europe/London`, `Asia/Tokyo`
  - Default: `UTC`

## 📦 Requirements

- Python 3.12+
- aiogram 3.20.0 (Telegram Bot API)
- asyncpg 0.30.0 (PostgreSQL driver)
- python-dotenv 1.2.2 (Environment management)

## 🏗️ Architecture

```
bot.py                 # Main entry point
├── config.py          # Environment & configuration
├── database/
│   ├── pg_db.py      # PostgreSQL operations
│   └── sqlite_db.py  # Deprecated stub
├── handlers/
│   ├── start.py      # /start command
│   ├── admin.py      # Welcome & button commands
│   ├── channels.py   # Channel management
│   ├── welcome.py    # New member handler
│   ├── callbacks.py  # Button callbacks
│   └── broadcast.py  # Broadcast system
├── keyboards/
│   └── inline.py     # Inline keyboards
├── filters/
│   └── admin.py      # Admin permission check
└── requirements.txt   # Dependencies
```

## 🗄️ Database Schema

PostgreSQL tables:

**welcome_messages**
```sql
CREATE TABLE welcome_messages (
    chat_id BIGINT PRIMARY KEY,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**buttons**
```sql
CREATE TABLE buttons (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    label TEXT NOT NULL,
    url TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_buttons_chat ON buttons(chat_id);
```

**channels** (informational only)
```sql
CREATE TABLE channels (
    id SERIAL PRIMARY KEY,
    channel_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    title TEXT,
    added_by BIGINT,
    added_at TIMESTAMPTZ DEFAULT NOW()
);
```

**known_chats** (broadcast targeting)
```sql
CREATE TABLE known_chats (
    chat_id BIGINT PRIMARY KEY,
    chat_type TEXT NOT NULL,
    title TEXT,
    username TEXT,
    registered_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_known_chats_type ON known_chats(chat_type);
```

## 🔍 Local Testing

```bash
# Clone repository
git clone https://github.com/YSs94za/Welcome---Bot.git
cd Welcome---Bot

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your BOT_TOKEN and DATABASE_URL

# Run bot
python bot.py
```

## 📊 Logs

Bot logs include:
- Startup/shutdown events
- User commands and interactions
- Welcome message deliveries
- Database operations
- Error traces

Configure via `LOG_LEVEL` environment variable.

## 🛡️ Error Handling

- ✅ Graceful Telegram API errors (BadRequest, FloodWait, Forbidden)
- ✅ Database connection retries
- ✅ Automatic cleanup of blocked chats
- ✅ Comprehensive logging for debugging
- ✅ Safe message fallbacks

## 🐛 Troubleshooting

### Bot won't start
- Check `BOT_TOKEN` is set correctly
- Check `DATABASE_URL` is valid
- Check Railway PostgreSQL plugin is attached
- View logs in Railway dashboard

### Welcome messages not sending
- Verify `/set_welcome` was successful
- Check bot has group admin permissions
- View logs for Telegram API errors

### Broadcast failing
- Ensure `BROADCAST_ADMIN_IDS` includes your user ID
- Check bot still has access to target chats
- View logs for permission/API errors

## 📄 License

MIT License — See LICENSE file

## 👨‍💻 Developer

**YOUSEF SHAHEEN**
- Telegram: [@Y9_S4](https://t.me/Y9_S4)
- Instagram: [@1.0_v_](https://www.instagram.com/1.0_v_)
- Ready to disrupt with automated solutions ⚡
