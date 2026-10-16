# Morning Brief

A daily Claude-powered brief for an Indian finance / markets Instagram page that
also covers current affairs. Every morning (about 6:00 AM IST) a scheduled
Claude run:

1. **collects** 12–20 candidate India (and India-relevant global) news stories,
2. **filters** them into **Proceed / Hold / Drop** — fresh, confirmed by 2
   credible sources or one official source, wide real-world impact, a clear
   "so what", no rumours / celebrity / communal / stock-tip content,
3. **sends 1–4 one-liners** (zero is fine) to your Telegram, each with its source,
4. **logs** the full list (with links) to `log/<date>.md`.

No analysis in the message — it is a topic list for your own research. The
wording is facts only, never buy/sell language.

## Install (the easy way)

Open Claude (desktop app) and say:

> Install https://github.com/Vickey-vijay/MorningBrief.git and follow its INSTALL.md

Claude will clone it, check Python, ask for your **Telegram chat id**, ask **you**
to set the **bot token** as an environment variable (it never sees the token),
send a test message and create the 6 AM scheduled task.

## Install (manual)

Needs Python 3.9+ and the Claude desktop app.

```
git clone https://github.com/Vickey-vijay/MorningBrief.git
cd MorningBrief
python setup.py --chat-id <your telegram chat id>
```

Set the bot token as an environment variable `BRIEF_BOT_TOKEN`
(Windows: `setx BRIEF_BOT_TOKEN "<token>"`, then fully restart the Claude app), then:

```
python setup.py --check --send-test
```

Finally create the scheduled task as described in step 7 of [INSTALL.md](INSTALL.md).

## Files

| File | What it is |
|---|---|
| `PROMPT.md` | The instructions the daily run follows (collect → classify → select → write → log → send). Edit the rules here. |
| `send_telegram.py` | Sends one message through the Telegram Bot API (standard library only). |
| `setup.py` | Writes `config.json` and runs a health check (`--check`, `--send-test`). |
| `config.example.json` | Template for `config.json` (git-ignored, holds your chat id). |
| `INSTALL.md` | Step-by-step install guide written for Claude to follow. |
| `state.json`, `log/` | Created on first run, git-ignored: stories already sent / on hold, and daily logs. |

## Secrets

The bot token lives only in an environment variable. `config.json` (chat id),
`state.json` and `log/` are git-ignored and never leave your computer.

## Known limits

- Claude's web tools cannot reach Economic Times, Mint, Moneycontrol, Reuters,
  The Hindu, BusinessLine and some others; results come mainly from Business
  Standard, Business Today, ThePrint, Free Press Journal, Outlook Business, All
  India Radio and PIB. See the search tips in `PROMPT.md`.
- The Claude app must be open and the computer awake at run time.
