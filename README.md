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

Once step 3 is done, this runs on GitHub's own servers on the real schedule in
`.github/workflows/market_pulse.yml`, whether your computer is on, off, or in a lake.

## Real proof-of-independence test

To prove this doesn't depend on your computer: after setup, shut your computer down fully (not
sleep — closed, powered off) during a real scheduled run window (10:00 AM / 12:30 PM / 2:30 PM /
3:45 PM ET on a weekday), then check your phone and the repo's **Actions** tab for a real run with
a matching timestamp while your machine was verifiably off.
