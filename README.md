# Markets Bot

Discord bot that tracks stocks for you. Slash commands to build a watchlist, check prices, and get DM updates every few hours.

## Commands

- `/track AAPL` — add a stock to your watchlist (pick an exchange if it's not US-listed)
- `/untrack AAPL` — remove one
- `/watchlist` — live prices for everything you're tracking
- `/price AAPL` — quick price check, doesn't save anything
- `/subscribe` / `/unsubscribe` — toggle DM updates
- `/status` — see your current settings
- `/help` — all of the above, in Discord

## Running it

```bash
pip install -r requirements.txt
cp .env.example .env   # then drop your bot token in
python main.py
```

## Discord setup

In the [Developer Portal](https://discord.com/developers/applications), on your app:

**Bot tab** — no privileged intents needed. The bot only uses slash commands and DMs, so leave Presence/Server Members/Message Content all off.

**Invite link** — OAuth2 → URL Generator:
- Scopes: `bot`, `applications.commands`
- Bot permissions: `Send Messages`, `Embed Links`, `Read Message History`

That's it — no admin, no manage server, nothing scary. The bot can't read your messages or moderate anything, it just posts price embeds.

## Updating the bot

After editing files, the usual loop:

```bash
git add .
git commit -m "describe what changed"
git push origin main
```

Want a safety net so a bad change doesn't land straight on main? Branch first:

```bash
git checkout -b some-feature
# make changes, test them
git add .
git commit -m "describe what changed"
git push -u origin some-feature
# then merge into main once you're happy, either via a GitHub PR or:
git checkout main
git merge some-feature
git push origin main
```

## Notes

- Per-user watchlist is capped at 15 tickers (`MAX_TICKERS_PER_USER` in `config.py`) so `/watchlist` stays fast.
- Price data comes from Yahoo Finance via `yfinance` — free, no API key, but not real-time-exchange-grade. Fine for a personal tracker, not for trading decisions.
