# 🤖 Raiden Shogun Discord Bot

A comprehensive Politics and War (PnW) management Discord bot with advanced features for alliance operations, nation analysis, and military planning.

## ✨ Features

### 🏛️ Nation Commands
- **`/who`** - Show basic nation information
- **`/warchest`** - Calculate warchest requirements (5 days)
- **`/wars`** - Show active wars and military
- **`/chest`** - Display current resources
- **`/military`** - Check military capacity and usage

### ⚔️ Raid Commands
- **`/raid`** - Find profitable raid targets in war range
- **`/purge`** - Find purge targets (purple nations <15 cities)
- **`/counter`** - Find alliance members to counter a target

### 🏛️ Alliance Commands
- **`/audit`** - Comprehensive member auditing (8 types)
- **`/bank`** - Check alliance bank balance

### ⚔️ War Commands
- **`/war`** - Show active wars for a nation

### 🛠️ Utility Commands
- **`/help`** - Get help with bot commands
- **`/ping`** - Check bot latency
- **`/register`** - Link Discord account to PnW nation
- **`/suggest`** - Submit suggestions
- **`/report-a-bug`** - Report bugs

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Discord Bot Token
- Politics and War API Keys

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd raiden_shogun
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   # Create .env file
   BOT_TOKEN=your_discord_bot_token
   GUILD_ID=your_discord_guild_id
   ADMIN_USER_ID=your_discord_user_id
   ALLIANCE_ID=13033
   ```

4. **Update API keys** in `bot/config/settings.py`

5. **Run the bot**:
   ```bash
   python3 bot/runner.py
   ```

## 🏗️ Architecture

The bot follows a clean, organized architecture:

```
bot/
├── config/           # Configuration management
├── models/           # Data models (Nation, Alliance, War, User)
├── services/         # Business logic layer
├── api/             # External API interactions with key rotation
├── cogs/            # Discord command groups
│   ├── nation/      # Nation commands (info, raid, search)
│   ├── alliance/    # Alliance commands (audit, management)
│   ├── war/         # War commands (detection, analysis)
│   └── utility/     # Utility commands (help, feedback)
├── utils/           # Helper functions and utilities
└── data/            # Data storage and cache
```

## 🔑 API Key Management

The bot uses an advanced 8-key rotation system:

- **Everything Scope** (2 keys): Nation data, war data, city data
- **Alliance Scope** (4 keys): Alliance operations, member data
- **Personal Scope** (1 key): Personal nation data only
- **Messaging Scope** (1 key): Future messaging features

This prevents rate limiting and ensures optimal performance.

## 📊 Advanced Features

### Smart Caching
- CSV-based data management
- 5-minute automatic updates
- Corrupted file recovery
- Memory-efficient storage

### Pagination System
- 3x3 grid layout for raid targets
- Navigation controls
- 5-minute timeout protection

### Comprehensive Auditing
- **Activity**: 24-hour inactivity detection
- **Warchest**: Resource deficit analysis
- **Spies**: Intelligence Agency compliance
- **Projects**: Minimum project requirements
- **Bloc**: Color bloc compliance
- **Military**: Capacity vs usage analysis
- **MMR**: Military Manufacturing Ratio
- **Deposit**: Excess resource detection

### Error Handling
- Graceful API failure recovery
- User-friendly error messages
- Comprehensive logging
- Automatic retry mechanisms

## 🧪 Testing

Run the comprehensive test suite:

```bash
python3 test_system.py
```

Tests cover:
- ✅ Module imports
- ✅ Configuration system
- ✅ Data models
- ✅ Service layer
- ✅ Utility functions

## 📈 Performance

- **Response Times**: < 1s for simple commands, < 5s for complex operations
- **Memory Usage**: ~70MB with full cache
- **API Capacity**: 8,000 calls/hour with key rotation
- **Cache Updates**: Every 5 minutes automatically

## 🔒 Security

- **Input Validation**: All user inputs sanitized
- **Permission System**: Role-based command access
- **Data Protection**: Only public PnW data stored
- **Secure Storage**: Environment variables for secrets

## 📚 Documentation

- **[Features & Commands](FEATURES_AND_COMMANDS.md)** - Detailed technical specifications
- **[Codebase Organization](CODEBASE_ORGANIZATION_RULES.md)** - Development guidelines
- **[Configuration Guide](CONFIGURATION.md)** - Setup instructions

## 🤝 Contributing

1. Follow the codebase organization rules
2. Keep files under 3,000 LoC
3. Maintain single responsibility principle
4. Add comprehensive tests
5. Update documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, suggestions, or bug reports:
- Use `/suggest` command in Discord
- Use `/report-a-bug` command in Discord
- Check the [Issues](https://github.com/your-repo/issues) page

---

**Built with ❤️ for the Politics and War community**




