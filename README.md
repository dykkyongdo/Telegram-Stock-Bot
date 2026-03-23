# 📈 Stock News Telegram Bot — Setup Guide

A personal Telegram bot that fetches AI-powered news summaries for your stock watchlist and sends you a daily morning briefing.

---

## What It Does

| Command | Description |
|---|---|
| `/portfolio` | View your current watchlist |
| `/add AAPL` | Add a stock to follow |
| `/remove AAPL` | Remove a stock |
| `/news` | Get latest AI news summary for all your stocks |
| `/help` | Show commands |

It also sends you an **automatic daily briefing every morning at 8:00 AM UTC**.

Your portfolio comes pre-loaded: `AMZN, NVDA, IREN, ONDS, SOFI, XEQT.TO, CGL-C.TO`

---

## Step 1 — Get Your Telegram Bot Token (2 minutes)

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Give your bot a name (e.g. `My Stock Bot`)
4. Give it a username ending in `bot` (e.g. `mystocks_news_bot`)
5. BotFather will give you a token like: `7123456789:AAFxxx...`
6. **Save this token** — you'll need it shortly

---

## Step 2 — Get Your Anthropic API Key (2 minutes)

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign in or create a free account
3. Go to **API Keys** → **Create Key**
4. **Save this key** — you'll need it shortly

---

## Step 3 — Get Your Telegram Chat ID (for daily alerts)

1. Search for **@userinfobot** on Telegram
2. Send it `/start`
3. It will reply with your **Chat ID** (a number like `123456789`)
4. **Save this number**

---

## Step 4 — Install Python (if you don't have it)

Download Python 3.11+ from [python.org](https://python.org/downloads)

Check it's installed:
```bash
python --version
```

---

## Step 5 — Install the Bot

1. Download and unzip the bot files into a folder (e.g. `stock-bot/`)

2. Open a terminal in that folder and run:
```bash
pip install -r requirements.txt
```

---

## Step 6 — Set Your Credentials

### On Mac/Linux:
```bash
export TELEGRAM_TOKEN="your_token_here"
export ANTHROPIC_API_KEY="your_anthropic_key_here"
export CHAT_ID="your_chat_id_here"
```

### On Windows (Command Prompt):
```cmd
set TELEGRAM_TOKEN=your_token_here
set ANTHROPIC_API_KEY=your_anthropic_key_here
set CHAT_ID=your_chat_id_here
```

### On Windows (PowerShell):
```powershell
$env:TELEGRAM_TOKEN="your_token_here"
$env:ANTHROPIC_API_KEY="your_anthropic_key_here"
$env:CHAT_ID="your_chat_id_here"
```

---

## Step 7 — Run the Bot!

```bash
python bot.py
```

You should see:
```
✅ Daily briefing scheduled at 08:00 UTC
🤖 Bot is running — press Ctrl+C to stop.
```

Now open Telegram, find your bot by its username, and send `/start`!

---

## Step 8 — Keep It Running 24/7 (Optional but Recommended)

If you want daily alerts, the bot needs to run continuously. Easiest option:

### Option A: Railway.app (Free, Recommended)
1. Create a free account at [railway.app](https://railway.app)
2. Click **New Project** → **Deploy from GitHub**
3. Push your bot files to a GitHub repo
4. In Railway, go to **Variables** and add your 3 environment variables
5. Deploy — it runs forever for free!

### Option B: Keep your PC on
Just leave the terminal window open with the bot running.

### Option C: Render.com (Free)
Similar to Railway — create account, connect GitHub, add environment variables.

---

## Adjusting the Daily Briefing Time

By default, the bot sends the briefing at **8:00 AM UTC**.

To change it, open `bot.py` and find this line:
```python
app.job_queue.run_daily(daily_briefing, time=time(hour=8, minute=0))
```

Change `hour=8` to your preferred hour in UTC.

| Your Timezone | UTC Offset | 8 AM local = UTC |
|---|---|---|
| Eastern (ET) | -5 / -4 | 13:00 / 12:00 |
| Pacific (PT) | -8 / -7 | 16:00 / 15:00 |
| **Vancouver/Burnaby (PT)** | **-8 / -7** | **16:00 / 15:00** |
| London (GMT) | 0 / +1 | 8:00 / 7:00 |

So if you're in **Burnaby, BC** and want your briefing at 8 AM, set `hour=15` (during PDT) or `hour=16` (during PST).

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| Bot not responding | Make sure `python bot.py` is running in your terminal |
| No daily alerts | Make sure `CHAT_ID` is set and bot is running 24/7 |
| `/news` times out | Try again — web search occasionally takes longer |

---

## Cost

- **Telegram bot:** Free forever
- **Anthropic API:** Each `/news` call costs ~$0.01–0.03 USD (very cheap)
- **Hosting on Railway:** Free tier is plenty for this bot

---

*Built with python-telegram-bot + Anthropic Claude*
