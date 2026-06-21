# Markets Bot

Discord bot that tracks stocks for you. Slash commands to build a watchlist, check prices, and get DM updates every few hours.
Uses Yahoo Finances free API, is avaliable to change to another.
## Commands
    /track — add a stock to your watchlist (pick an exchange if it's not US-listed)
    /untrack — remove one
    /watchlist — live prices for everything you're tracking
    /price — quick price check, doesn't save anything
    /subscribe / /unsubscribe — toggle DM updates
    /status — see your current settings
    /help — all of the above, in Discord

## Running it
    git clone https://github.com/Larpetsu/Market-Tracker.git
    pip install -r requirements.txt
    cp .env.example .env   # then drop your bot token in   
    python main.py

## Discord setup

In the Developer Portal, on your app:

Bot tab — no privileged intents needed. The bot only uses slash commands and DMs, so leave Presence/Server Members/Message Content all off.

Invite link — OAuth2 → URL Generator:

    Scopes: bot, applications.commands
    Bot permissions: Send Messages, Embed Links, Read Message History
## Notes

    Per-user watchlist is capped at 15 tickers (MAX_TICKERS_PER_USER in config.py) so /watchlist stays fast.
    Price data comes from Yahoo Finance via yfinance — free, no API key, but not real-time-exchange-grade. Fine for a personal tracker, not for trading decisions.
