"""
Stock News Telegram Bot
-----------------------
Commands:
  /start      - welcome + help
  /help       - same as start
  /portfolio  - view your watchlist
  /add TICKER - add a stock
  /remove TICKER - remove a stock
  /news       - AI-powered news summary for all your stocks
"""

import os
import json
import logging
import asyncio
from datetime import time

import anthropic
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Config
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ANTHROPIC_KEY  = os.environ["ANTHROPIC_API_KEY"]
CHAT_ID        = os.environ.get("CHAT_ID", "")
WATCHLIST_FILE = "watchlist.json"

DEFAULT_STOCKS = ["AMZN", "NVDA", "IREN", "ONDS", "SOFI", "XEQT", "CGL.C"]

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)


# Watchlist helpers
def load_watchlist() -> list[str]:
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE) as f:
            return json.load(f).get("stocks", DEFAULT_STOCKS.copy())
    return DEFAULT_STOCKS.copy()


def save_watchlist(stocks: list[str]) -> None:
    with open(WATCHLIST_FILE, "w") as f:
        json.dump({"stocks": stocks}, f, indent=2)


# AI news fetcher
def fetch_news_summary(stocks: list[str]) -> str:
    tickers = ", ".join(stocks)

    messages = [
        {
            "role": "user",
            "content": (
                f"Search today's news for these stocks: {tickers}\n\n"
                "Notes: CGL.C = iShares Gold Bullion ETF Canada. XEQT = iShares Core Equity ETF Canada.\n\n"
                "For each stock, plain text only, no markdown, no asterisks, no hashtags:\n\n"
                "TICKER - Name\n"
                "Sentiment: one of Bullish / Bearish / Neutral (with emoji)\n"
                "News: one key headline\n"
                "Tip: one sentence for a long-term investor\n"
                "---"
            ),
        }
    ]

    while True:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=(
                "You are a concise financial news assistant for a retail investor. "
                "Always search the web for the latest news before answering. "
                "Use plain text only — no markdown, no bold, no headers."
            ),
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=messages,
        )

        text_parts = [
            b.text for b in resp.content if hasattr(b, "text") and b.text
        ]

        if resp.stop_reason == "end_turn":
            return "\n\n".join(text_parts) or "No summary available."

        if resp.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": resp.content})
            tool_results = [
                {
                    "type": "tool_result",
                    "tool_use_id": b.id,
                    "content": "",
                }
                for b in resp.content
                if b.type == "tool_use"
            ]
            messages.append({"role": "user", "content": tool_results})
        else:
            return "\n\n".join(text_parts) or "Unexpected response."


# Command handlers
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    stocks = load_watchlist()
    await update.message.reply_text(
        "👋 Stock News Bot\n\n"
        "Commands:\n\n"
        "📊 /portfolio — view your watchlist\n"
        "➕ /add TICKER — add a stock (e.g. /add AAPL)\n"
        "➖ /remove TICKER — remove a stock\n"
        "📰 /news — get AI news summary\n"
        "❓ /help — show this message\n\n"
        f"Your watchlist: {', '.join(stocks)}",
    )


async def cmd_portfolio(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    stocks = load_watchlist()
    if not stocks:
        await update.message.reply_text("Watchlist is empty. Use /add TICKER to get started.")
        return
    lines = "\n".join(f"  - {s}" for s in stocks)
    await update.message.reply_text(f"Your Watchlist ({len(stocks)} stocks)\n\n{lines}")


async def cmd_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not ctx.args:
        await update.message.reply_text("Usage: /add TICKER\nExample: /add AAPL")
        return
    ticker = ctx.args[0].upper()
    stocks = load_watchlist()
    if ticker in stocks:
        await update.message.reply_text(f"{ticker} is already in your watchlist!")
        return
    stocks.append(ticker)
    save_watchlist(stocks)
    await update.message.reply_text(f"✅ {ticker} added!")


async def cmd_remove(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not ctx.args:
        await update.message.reply_text("Usage: /remove TICKER\nExample: /remove AAPL")
        return
    ticker = ctx.args[0].upper()
    stocks = load_watchlist()
    if ticker not in stocks:
        await update.message.reply_text(f"{ticker} is not in your watchlist.")
        return
    stocks.remove(ticker)
    save_watchlist(stocks)
    await update.message.reply_text(f"❌ {ticker} removed.")


async def cmd_news(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    stocks = load_watchlist()
    if not stocks:
        await update.message.reply_text("Watchlist is empty. Use /add TICKER to add stocks.")
        return
    await update.message.reply_text(f"🔍 Searching news for {len(stocks)} stocks... hang tight!")
    loop = asyncio.get_event_loop()
    try:
        summary = await loop.run_in_executor(None, fetch_news_summary, stocks)
        if len(summary) > 4000:
            chunks = [summary[i:i+4000] for i in range(0, len(summary), 4000)]
            for i, chunk in enumerate(chunks):
                header = "📰 News Summary\n\n" if i == 0 else ""
                await update.message.reply_text(header + chunk)
        else:
            await update.message.reply_text(f"📰 News Summary\n\n{summary}")
    except Exception:
        logger.exception("Error fetching news")
        await update.message.reply_text("⚠️ Something went wrong. Please try again.")


# Daily briefing
async def daily_briefing(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not CHAT_ID:
        return
    stocks = load_watchlist()
    if not stocks:
        return
    loop = asyncio.get_event_loop()
    try:
        summary = await loop.run_in_executor(None, fetch_news_summary, stocks)
        msg = f"🌅 Good Morning — Daily Stock Briefing\n\n{summary}"
        if len(msg) > 4000:
            chunks = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
            for chunk in chunks:
                await ctx.bot.send_message(chat_id=CHAT_ID, text=chunk)
        else:
            await ctx.bot.send_message(chat_id=CHAT_ID, text=msg)
    except Exception:
        logger.exception("Daily briefing failed")


# Main
def main() -> None:
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("help",      cmd_start))
    app.add_handler(CommandHandler("portfolio", cmd_portfolio))
    app.add_handler(CommandHandler("add",       cmd_add))
    app.add_handler(CommandHandler("remove",    cmd_remove))
    app.add_handler(CommandHandler("news",      cmd_news))

    # 15:00 UTC = 8:00 AM Vancouver PDT (change to 16 during PST Nov-Mar)
    if CHAT_ID:
        app.job_queue.run_daily(daily_briefing, time=time(hour=15, minute=0))
        logger.info("✅ Daily briefing scheduled at 15:00 UTC")

    logger.info("🤖 Bot is running!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
