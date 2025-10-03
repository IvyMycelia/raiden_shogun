# 🔧 Configuration Guide

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# Discord Bot Configuration
BOT_TOKEN=your_discord_bot_token_here
GUILD_ID=your_discord_guild_id_here
ADMIN_USER_ID=your_discord_user_id_here

# Politics and War Configuration
ALLIANCE_ID=13033

# Optional: Override default settings
# CACHE_UPDATE_INTERVAL=300
# API_RATE_LIMIT=1000
# API_DELAY=0.5
```

## Required Variables

- **BOT_TOKEN**: Your Discord bot token from the Discord Developer Portal
- **GUILD_ID**: The Discord server ID where the bot will operate
- **ADMIN_USER_ID**: Your Discord user ID for admin commands
- **ALLIANCE_ID**: The Politics and War alliance ID (default: 13033)

## API Keys

The bot uses 8 API keys for Politics and War. Update the keys in `bot/config/settings.py`:

```python
API_KEYS = {
    "everything_scope": [
        "your_everything_key_1",
        "your_everything_key_2"
    ],
    "alliance_scope": [
        "your_alliance_key_1",
        "your_alliance_key_2",
        "your_alliance_key_3",
        "your_alliance_key_4"
    ],
    "personal_scope": [
        "your_personal_key"
    ],
    "messaging_scope": [
        "your_messaging_key"
    ]
}
```

## Setup Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   - Copy the environment variables above to a `.env` file
   - Update the API keys in `bot/config/settings.py`

3. **Run the Bot**:
   ```bash
   python3 bot/runner.py
   ```

## Features

The bot includes all features from the original implementation:

- **Nation Commands**: `/who`, `/warchest`, `/wars`, `/chest`, `/military`
- **Raid Commands**: `/raid`, `/purge`, `/counter`
- **Alliance Commands**: `/audit`, `/bank`
- **War Commands**: `/war`
- **Utility Commands**: `/help`, `/ping`, `/register`, `/suggest`, `/report-a-bug`

## Architecture

The bot follows a clean architecture pattern:

- **Models**: Data structures for Nation, Alliance, War, User
- **Services**: Business logic layer
- **API**: External API interactions with key rotation
- **Cogs**: Discord command groups
- **Utils**: Helper functions and utilities

## Testing

Run the test suite to verify everything works:

```bash
python3 test_system.py
```

All tests should pass before running the bot in production.
