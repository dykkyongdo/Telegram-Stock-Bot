"""
Stock News Telegram Bot
-----------------------
Commands:
  /start      — welcome + help
  /help       — same as start
  /portfolio  — view your watchlist
  /add TICKER — add a stock
  /remove TICKER — remove a stock
  /news       — AI-powered news summary for all your stocks
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

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]       # from BotFather
ANTHROPIC_KEY  = os.environ["ANTHROPIC_API_KEY"]    # from console.anthropic.com
CHAT_ID        = os.environ.get("CHAT_ID", "")      # your Telegram user ID (for daily alerts)
WATCHLIST_FILE = "watchlist.json"

# Your current portfolio pre-loaded as defaults
DEFAULT_STOCKS = ["AMZN", "NVDA", "IREN", "ONDS", "SOFI", "XEQT", "CGL.C"]

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)


# ── Watchlist helpers ─────────────────────────────────────────────────────────
def load_watchlist() -> list[str]:
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE) as f:
            return json.load(f).get("stocks", DEFAULT_STOCKS.copy())
    return DEFAULT_STOCKS.copy()


def save_watchlist(stocks: list[str]) -> None:
    with open(WATCHLIST_FILE, "w") as f:
        json.dump({"stocks": stocks}, f, indent=2)


# ── AI news fetcher ───────────────────────────────────────────────────────────
def fetch_news_summary(stocks: list[str]) -> str:
    """Use Claude + web search to get today's news for each stock."""
    tickers = ", ".join(stocks)

    messages = [
        {
            "role": "user",
            "content": (
                f"Search for the very latest news (today) for each of these stocks: {tickers}.\n\n"
                "IMPORTANT TICKER NOTES:\n"
                "- CGL.C = iShares Gold Bullion ETF (CAD-hedged) on TSX — NOT Cervus Equipment\n"
                "- XEQT = iShares Core Equity ETF Portfolio on TSX\n\n"
                "For EACH stock output EXACTLY this format. Use NO markdown, NO **, NO ##, NO bullet points:\n\n"
                "TICKER - Company Name\n"
                "Sentiment: 🟢 Bullish  (or 🔴 Bearish or 🟡 Neutral)\n"
                "News: headline one\n"
                "News: headline two\n"
                "Tip: one sentence on what this means for a long-term investor\n"
                "────────────────────\n\n"
                "Keep it clean and simple. Plain text only. No asterisks, no hashtags, no extra formatting."
            ),
        }
    ]

    # Handle the tool-use loop (web_search may run multiple times)
    while True:
        resp = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=(
                "You are a concise financial news assistant for a retail investor. "
                "Always search the web for the latest news before answering. "
                "Summaries must be short, clear, and actionable."
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
            return "\n\n".join(text_parts) or "Unexpected response from AI."


# ── Command handlers ──────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    stocks = load_watchlist()
    await update.message.reply_text(
        "👋 *Stock News Bot*\n\n"
        "Here's what I can do:\n\n"
        "📊 /portfolio — view your watchlist\n"
        "➕ /add TICKER — add a stock  _(e.g. /add AAPL)_\n"
        "➖ /remove TICKER — remove a stock\n"
        "📰 /news — get AI-powered news summary\n"
        "❓ /help — show this message\n\n"
        f"Your current watchlist: `{', '.join(stocks)}`",
        parse_mode="Markdown",
    )


async def cmd_portfolio(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    stocks = load_watchlist()
    if not stocks:
        await update.message.reply_text("Your watchlist is empty. Use /add TICKER to get started.")
        return
    lines = "\n".join(f"  • {s}" for s in stocks)
    await update.message.reply_text(
        f"📊 *Your Watchlist* ({len(stocks)} stocks)\n\n{lines}",
        parse_mode="Markdown",
    )


async def cmd_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not ctx.args:
        await update.message.reply_text("Usage: /add TICKER\nExample: /add AAPL")
        return
    ticker = ctx.args[0].upper()
    stocks = load_watchlist()
    if ticker in stocks:
        await update.message.reply_text(f"*{ticker}* is already in your watchlist! ✅", parse_mode="Markdown")
        return
    stocks.append(ticker)
    save_watchlist(stocks)
    await update.message.reply_text(f"✅ *{ticker}* has been added to your watchlist!", parse_mode="Markdown")


async def cmd_remove(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not ctx.args:
        await update.message.reply_text("Usage: /remove TICKER\nExample: /remove AAPL")
        return
    ticker = ctx.args[0].upper()
    stocks = load_watchlist()
    if ticker not in stocks:
        await update.message.reply_text(f"*{ticker}* is not in your watchlist.", parse_mode="Markdown")
        return
    stocks.remove(ticker)
    save_watchlist(stocks)
    await update.message.reply_text(f"❌ *{ticker}* has been removed from your watchlist.", parse_mode="Markdown")


async def cmd_news(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    stocks = load_watchlist()
    if not stocks:
        await update.message.reply_text("Your watchlist is empty. Use /add TICKER to add stocks.")
        return
    await update.message.reply_text(
        f"🔍 Searching news for {len(stocks)} stocks… this takes ~15 seconds, hang tight!"
    )
    loop = asyncio.get_event_loop()
    try:
        summary = await loop.run_in_executor(None, fetch_news_summary, stocks)
        # Telegram has a 4096 char limit — split if needed
        if len(summary) > 4000:
            chunks = [summary[i:i+4000] for i in range(0, len(summary), 4000)]
            for i, chunk in enumerate(chunks):
                header = "📰 *News Summary*\n\n" if i == 0 else ""
                await update.message.reply_text(header + chunk, parse_mode="Markdown")
        else:
            await update.message.reply_text(f"📰 *News Summary*\n\n{summary}", parse_mode="Markdown")
    except Exception:
        logger.exception("Error fetching news")
        await update.message.reply_text("⚠️ Something went wrong fetching the news. Please try again in a moment.")


# ── Daily briefing job ────────────────────────────────────────────────────────
async def daily_briefing(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Runs every morning at 8:00 AM UTC and sends a news summary."""
    if not CHAT_ID:
        logger.info("No CHAT_ID set — skipping daily briefing.")
        return
    stocks = load_watchlist()
    if not stocks:
        return
    loop = asyncio.get_event_loop()
    try:
        summary = await loop.run_in_executor(None, fetch_news_summary, stocks)
        msg = f"🌅 *Good Morning — Daily Stock Briefing*\n\n{summary}"
        if len(msg) > 4000:
            chunks = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
            for chunk in chunks:
                await ctx.bot.send_message(chat_id=CHAT_ID, text=chunk, parse_mode="Markdown")
        else:
            await ctx.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")
    except Exception:
        logger.exception("Daily briefing failed")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("help",      cmd_start))
    app.add_handler(CommandHandler("portfolio", cmd_portfolio))
    app.add_handler(CommandHandler("add",       cmd_add))
    app.add_handler(CommandHandler("remove",    cmd_remove))
    app.add_handler(CommandHandler("news",      cmd_news))

    # Schedule daily briefing at 8:00 AM UTC (adjust hour to your timezone)
    if CHAT_ID:
        app.job_queue.run_daily(daily_briefing, time=time(hour=8, minute=0))
        logger.info("✅ Daily briefing scheduled at 08:00 UTC")

    logger.info("🤖 Bot is running — press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
