# Market Pulse (cloud-independent notifier)

Runs entirely on GitHub Actions. Not connected to your computer, Claude Code, or the local
Portfolio Tracker's data in any way — this is the actual, final answer to phone notifications that
don't depend on your machine being on.

## What it does

Every run: fetches real live quotes for your holdings + SPY/QQQ/VIX from Yahoo Finance's public
(keyless) endpoint, flags any real mover beyond ±3%, pulls that ticker's real top headline, and
sends it all as one Telegram message.

**Real, deliberate limitation:** this repo has no access to your local holdings data (that's the
point — zero local dependency). The ticker list is hardcoded in `market_pulse.py`'s `WATCHLIST` —
update it by hand in this repo whenever your real holdings change materially.

**Real data-source caveat:** Yahoo's chart/RSS endpoints are public but unofficial. They could
rate-limit or change without notice — if messages stop arriving, that's the first thing to check.

## One-time setup (you do this part — I can't create a GitHub repo or hold your token for you)

1. Go to github.com → **New repository** → any name (e.g. `market-pulse`) → **Create** (public or
   private, doesn't matter).
2. On your own machine, from this `cloud_notify` folder:
   ```
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git branch -M main
   git push -u origin main
   ```
3. In the new repo on github.com: **Settings → Secrets and variables → Actions → New repository
   secret**. Add two:
   - `TELEGRAM_BOT_TOKEN` — the same value your local `.env`/environment already has.
   - `TELEGRAM_CHAT_ID` — same as above.
4. Go to the **Actions** tab → "Market Pulse" workflow → **Run workflow** (manual trigger) to test
   it immediately, before waiting for the real schedule.

## Splitting into separate chats (optional, 2026-09-02)

By default everything still goes to `TELEGRAM_CHAT_ID`. To route broad market context, mover
price/% lines, and mover news summaries into their own chats instead, add up to three more repo
secrets (any you skip just keeps falling back to `TELEGRAM_CHAT_ID`):

- `TELEGRAM_CHAT_ID_MARKET_NEWS` — broad market header (SPY/QQQ/VIX)
- `TELEGRAM_CHAT_ID_MOVEMENTS` — mover ticker/price/% lines
- `TELEGRAM_CHAT_ID_STOCK_NEWS` — mover news summaries

**How to create a new chat and find its chat id** (Telegram only lets the bot's owner do this, not
Claude):
1. In Telegram, create a new group (or channel) for the category, e.g. "Portfolio – Movements".
2. Add your existing bot to it as a member (search its @username the same way you'd add a person).
3. Send any real message in that new group (Telegram won't register the chat until it has at
   least one message).
4. In a browser, go to `https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getUpdates` (swap in your
   real bot token). Find the entry for the new group's message and copy its `"chat":{"id": ...}`
   value (group/channel ids are negative numbers).
5. Set that number as `TELEGRAM_CHAT_ID_MOVEMENTS` (or `_MARKET_NEWS` / `_STOCK_NEWS`) as a GitHub
   Actions repo secret here, AND as a local Windows env var (`setx TELEGRAM_CHAT_ID_MOVEMENTS
   "<the id>"`, new terminal needed for it to take effect) — same name, same value, for the local
   scripts that also route through it.

The same three secrets/env vars, with the same names, are shared by the local scripts:
`price_threshold_alerts.py` uses `TELEGRAM_CHAT_ID_MOVEMENTS`; `news_monitor.py` and
`regime_classifier.py` use `TELEGRAM_CHAT_ID_MARKET_NEWS`/`TELEGRAM_CHAT_ID_STOCK_NEWS`;
`daily_brief.py`/`weekly_brief.py` use `TELEGRAM_CHAT_ID_BRIEFS` (optional — briefs default to
staying in your original `TELEGRAM_CHAT_ID` chat unless you also create a dedicated one).

Once step 3 is done, this runs on GitHub's own servers on the real schedule in
`.github/workflows/market_pulse.yml`, whether your computer is on, off, or in a lake.

## Real proof-of-independence test

To prove this doesn't depend on your computer: after setup, shut your computer down fully (not
sleep — closed, powered off) during a real scheduled run window (10:00 AM / 12:30 PM / 2:30 PM /
3:45 PM ET on a weekday), then check your phone and the repo's **Actions** tab for a real run with
a matching timestamp while your machine was verifiably off.
