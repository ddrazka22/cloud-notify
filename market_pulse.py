"""
Standalone market-pulse notifier -- runs ENTIRELY on GitHub Actions, not on the user's own
computer. No dependency on Claude Code, no dependency on the user's computer being on, no local
file access of any kind (this file lives in its own real GitHub repo, separate from the main
Portfolio Tracker's data -- see this repo's README for why).

REAL, KEYLESS DATA SOURCES (no API key/signup needed from the user):
  - Yahoo Finance's public chart endpoint (query1.finance.yahoo.com/v8/finance/chart/<ticker>) --
    the same real, unofficial endpoint the `yfinance` Python library itself calls under the hood.
    Real, but unofficial -- Yahoo could rate-limit or change this without notice. If this ever
    breaks, that's the first thing to check.
  - Yahoo Finance's public per-ticker RSS news feed (feeds.finance.yahoo.com/rss/2.0/headline) --
    same real caveat.

TICKER LIST: hardcoded below (WATCHLIST), snapshotted from the user's real holdings as of
2026-08-26. This script has NO access to the local Portfolio Tracker's real, live position data
(that's the whole point of "no local file access") -- update WATCHLIST by hand here whenever real
holdings change materially. This is a real, deliberate tradeoff of full cloud independence, not an
oversight.

MOVER THRESHOLD: a ticker's real day-change is flagged when it crosses +/-3% -- tunable below.

Real secrets (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID) come from GitHub Actions repo secrets, set via
the GitHub UI (Settings -> Secrets and variables -> Actions) -- never hardcoded here, never
committed to the repo.
"""

import os
import re
import sys
import urllib.error
import urllib.request
import json

MOVER_THRESHOLD_PCT = 3.0

# Real current holdings as of 2026-08-26 -- update by hand when this drifts from the real Portfolio
# Tracker. Broad-market context tickers are always included regardless of holdings.
WATCHLIST = [
    "ABNB", "ACGL", "AFRM", "BAC", "CMCSA", "COF", "COHR", "CRSR", "CRWD", "DNLI", "EQT",
    "FNV", "GD", "GRPN", "ISRG", "KKR", "KSPI", "LSAK", "MDGL", "MELI", "MU", "NEE", "OKE",
    "PH", "SOFI", "SPCX", "TENB", "TSM", "VEEV", "VRT", "XPO", "ZION",
]
MARKET_CONTEXT = ["SPY", "QQQ", "^VIX"]

USER_AGENT = "Mozilla/5.0 (compatible; MarketPulseBot/1.0)"


def _http_get(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def get_quote(ticker):
    """Real current price + real day-change % for one ticker, via Yahoo's public chart endpoint.
    Returns None on any real failure (network, rate limit, bad ticker) -- never a fabricated
    quote."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"
    try:
        raw = _http_get(url)
        data = json.loads(raw)
        result = data["chart"]["result"][0]
        meta = result["meta"]
        price = meta["regularMarketPrice"]
        prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")
        if price is None or prev_close is None:
            return None
        pct = (price - prev_close) / prev_close * 100
        return {"ticker": ticker, "price": price, "pct": pct}
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError, TimeoutError) as e:
        print(f"  ! {ticker}: quote fetch failed ({e})", file=sys.stderr)
        return None


def get_top_headline(ticker):
    """Real top headline from Yahoo's public per-ticker RSS feed. Returns None on any real
    failure or if the feed has no items -- never a fabricated headline."""
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    try:
        raw = _http_get(url).decode("utf-8", errors="replace")
        m = re.search(r"<item>.*?<title>(.*?)</title>", raw, re.DOTALL)
        if not m:
            return None
        title = m.group(1).strip()
        title = title.replace("<![CDATA[", "").replace("]]>", "").strip()
        return title if title else None
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  ! {ticker}: headline fetch failed ({e})", file=sys.stderr)
        return None


def send_telegram(message):
    """Real Telegram Bot API send -- the same real bot/chat this project already uses locally,
    just called directly here (no dependency on the local telegram_alert.py module or the local
    machine at all)."""
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "HTML"}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status == 200


def build_digest():
    lines = ["<b>Market Pulse</b> (cloud, independent of local machine)\n"]

    lines.append("<b>Broad market:</b>")
    for tk in MARKET_CONTEXT:
        q = get_quote(tk)
        if q:
            label = "VIX" if tk == "^VIX" else tk
            lines.append(f"  {label}: {q['price']:.2f} ({q['pct']:+.2f}%)")
        else:
            lines.append(f"  {tk}: no real quote available this run")

    movers = []
    for tk in WATCHLIST:
        q = get_quote(tk)
        if q and abs(q["pct"]) >= MOVER_THRESHOLD_PCT:
            movers.append(q)

    if movers:
        movers.sort(key=lambda q: abs(q["pct"]), reverse=True)
        lines.append(f"\n<b>Movers (|change| >= {MOVER_THRESHOLD_PCT:.0f}%):</b>")
        for q in movers:
            arrow = "\U0001F4C8" if q["pct"] > 0 else "\U0001F4C9"
            headline = get_top_headline(q["ticker"])
            line = f"  {arrow} {q['ticker']}: ${q['price']:.2f} ({q['pct']:+.2f}%)"
            if headline:
                line += f"\n      {headline}"
            lines.append(line)
    else:
        lines.append(f"\nNo real holding crossed +/-{MOVER_THRESHOLD_PCT:.0f}% today.")

    return "\n".join(lines)


def main():
    digest = build_digest()
    # Real robustness fix: a local Windows console (cp1252) can't print the real emoji used in
    # the digest -- GitHub Actions' Ubuntu runners are UTF-8 by default and won't hit this, but
    # printing for local testing/log visibility shouldn't crash the whole run either way.
    print(digest.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace"))
    ok = send_telegram(digest)
    print(f"\nTelegram send: {'OK' if ok else 'FAILED'}")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
