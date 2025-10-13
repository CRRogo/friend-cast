# Discord Bot - Friend Cast

A minimal Discord bot built with `discord.py` 2.x using slash commands.

## Features

- /ping slash command returns latency
- Loads environment variables from .env
- Simple, production-ready structure with logging

## Prerequisites

- Python 3.10+
- A Discord Application and Bot token
- The bot must be invited to your server with the applications.commands scope

## Setup

1. Install dependencies:

```powershell
py -3 -m pip install -r requirements.txt
```

2. Create a .env file (see .env.example) and add your bot token:

```
DISCORD_TOKEN=your-bot-token-here
DISCORD_GUILD_ID=123456789012345678
```

3. Run the bot:

```powershell
py -3 bot.py
```

On first run, commands are synced. Global sync can take up to a minute. For instant availability, set `DISCORD_GUILD_ID` in your `.env` and the bot will sync commands only to that guild during development.

```python
# Replace setup_hook with this for a specific guild
GUILD_ID = 123456789012345678
async def setup_hook(self) -> None:
    guild = discord.Object(id=GUILD_ID)
    self.tree.copy_global_to(guild=guild)
    await self.tree.sync(guild=guild)
```

## Environment

Create .env (or set OS env vars):

```
DISCORD_TOKEN=your-bot-token
DISCORD_GUILD_ID=your-guild-id  # optional, speeds up slash command updates
```

## Inviting the Bot

1. In the Discord Developer Portal, open your Application → OAuth2 → URL Generator.
2. Scopes: check bot and applications.commands.
3. Bot Permissions: at least Send Messages and Use Slash Commands.
4. Open the generated URL and invite the bot to your server.

## Notes

- Global command sync can take time. Prefer guild-specific sync while iterating.
- Keep your token secret. Never commit .env.

## License

MIT


