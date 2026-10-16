# Install guide — written for Claude to follow

The person you are helping has asked you to install the **Morning Brief** from
this repository. It runs every morning, finds the few India current-affairs
stories worth a post, and sends them as one-liners to their Telegram.

You need exactly **two things** from them:

1. their **Telegram chat id** — a number, not secret; you may take it in chat;
2. the **Telegram bot token** — a secret. **Do not ask them to paste it into
   this chat, and never write it into any file.** They set it as an environment
   variable themselves (step 4).

Everything else you do yourself. Ask the person before steps 1 and 7 (they
change their computer), and tell them what you are about to do.

## 1. Get the files

Default location: `~/MorningBrief` (on Windows `%USERPROFILE%\MorningBrief`).
Ask whether they want a different folder. If you are already inside a clone of
this repo, use it as it is.

```
git clone https://github.com/Vickey-vijay/MorningBrief.git <INSTALL_DIR>
```

Use the absolute path of that folder wherever `<INSTALL_DIR>` appears below.

## 2. Check Python

Run `python --version` (or `py --version` / `python3 --version`). Need **3.9 or
newer**. If it is missing or too old, tell them to install Python from
python.org (tick "Add Python to PATH"), then stop and resume after they confirm.

## 3. Ask for the chat id, then write the config

Ask: *"What is your Telegram chat id?"* If they don't know it: in Telegram,
message **@userinfobot** — it replies with a number. They must also open **the
bot they were given** and press **Start** once, or the bot is not allowed to
message them.

Then, from `<INSTALL_DIR>`:

```
python setup.py --chat-id <THEIR_CHAT_ID>
```

This creates `config.json` (git-ignored, stays on this computer). Expect it to
end with "NOT READY" at this point because the token is not set yet — that is
normal.

## 4. The bot token — the person does this, not you

Tell them to set the token as an environment variable named `BRIEF_BOT_TOKEN`
(the name is `tokenEnvVar` in `config.json`). Give them the command for their
system and let them run it in their own terminal:

- **Windows (PowerShell):** `setx BRIEF_BOT_TOKEN "<paste token here>"`
- **macOS / Linux:** add `export BRIEF_BOT_TOKEN="<paste token here>"` to
  `~/.zshrc` or `~/.bashrc`

Then they must **fully quit and reopen the Claude app** — a new terminal is not
enough, because scheduled runs inherit the app's environment. Wait for them to
say it is done.

If the person prefers, whoever set this up for them can paste the chat id and
token on their behalf instead (`python setup.py --chat-id <id>` and the command
above). Either way you never see the token.

## 5. Verify and send a test message

```
python setup.py --check --send-test
```

It must end with `READY`, and a test message should arrive in their Telegram.
Ask them to confirm they received it. If it says the environment variable is
not set, the app was not fully restarted — ask them to quit and reopen it, then
run this again. The error text says what is wrong: a 401/404 means the token is
wrong, a 400/403 means the chat id is wrong or they have not pressed Start on
the bot.

## 6. Check the time zone

The brief is built for India time. Run `python -c "import time;print(time.tzname)"`
or check the OS clock. If the computer is not on India Standard Time, convert
`05:45 IST` to local time for the schedule in step 7 and tell the person.

## 7. Create the scheduled task

Use the scheduled-tasks tool in the Claude desktop app (`create_scheduled_task`,
or the `schedule` skill). Ask the person first. Settings:

- **taskId:** `morning-brief`
- **title:** `Morning Brief`
- **description:** `Daily 6 AM India current-affairs one-liners sent to Telegram.`
- **cronExpression:** `45 5 * * *` (local time). The scheduler adds a few
  minutes, so it starts about 5:55 and the message lands around 6:00–6:10.
- **prompt** (replace `<INSTALL_DIR>` with the absolute path):

```
You are running the daily "Morning Brief" for an Indian finance Instagram page.

The whole project is in this folder: <INSTALL_DIR>

1. Read PROMPT.md in that folder, then follow it exactly, step by step. It covers collecting news, filtering it into Proceed / Hold / Drop, logging, and sending.
2. Run every command with that folder as the working directory (cd into it first). Use `python send_telegram.py ...` as PROMPT.md describes (if `python` is not found, try `py` or `python3`).
3. config.json decides where the message goes (the owner's own Telegram chat). Never edit config.json and never send a message any other way.
4. If anything blocks you (a tool is unavailable, a search keeps failing, the send fails), write what happened into log/<today>.md and end the run with a plain statement of the failure. Do not guess at facts to fill a gap: if you could not verify a story, it goes to Hold.
5. Finish with one short line stating how many items were sent (0-4) and whether the Telegram send succeeded.
```

## 8. Run it once now

Use "Run now" on the task (`run_scheduled_task`). Tell the person first: this
sends a real first brief to their Telegram, and the app may ask them to approve
tools (web search, running Python). They should **approve** them — otherwise
the unattended 5:55 AM run can get stuck waiting for a click. Afterwards check
`log/<today>.md` and `log/send.log`.

## 9. Tell the person how it works from here

- The Claude app must be **open** and the computer **awake** around 5:55 AM.
  If the app was closed, the run happens when it next opens.
- Each day's full list (what was sent, held and dropped, with source links) is
  in `log/<date>.md`.
- To change what counts as post-worthy, edit the rules in `PROMPT.md`; to
  change the number of items, edit `maxItems` in `config.json`.
- To pause it, disable the `morning-brief` task in the app's Scheduled list.
- Updating later: `git pull` inside the folder (their `config.json`, `state.json`
  and `log/` are git-ignored and untouched).

## Rules for you

- Never print, echo, store or ask for the bot token. Never commit `config.json`.
- Only `send_telegram.py` sends messages, and only to the chat in `config.json`.
- If a step fails, say exactly which one and what the message was — don't work
  around it silently.
