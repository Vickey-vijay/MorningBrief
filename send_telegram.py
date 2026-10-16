#!/usr/bin/env python3
"""Send one Telegram message for the Morning Brief.

Dumb delivery only: the scheduled Claude run decides WHAT to say, this script
just sends it. Standard library only, so it runs on any OS with Python 3.9+.

Config comes from config.json next to this file:
  mode          "pilot" -> send to pilotChatId, "live" -> send to liveChatId
  tokenEnvVar   name of the environment variable holding the bot token
                (the token itself is never stored in any file)

Examples:
  python send_telegram.py --file log/2026-10-18.message.txt --marker log/2026-10-18.sent
  python send_telegram.py --message "hello" --dry-run
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAX_LEN = 4096  # Telegram's hard limit for one text message


def log(line):
    """Append one status line to log/send.log (never contains the token)."""
    try:
        (HERE / "log").mkdir(exist_ok=True)
        with open(HERE / "log" / "send.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat(timespec='seconds')} {line}\n")
    except OSError:
        pass


def fail(msg, code=1):
    log(f"FAIL {msg}")
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--message", help="text to send")
    src.add_argument("--file", help="UTF-8 text file holding the message")
    ap.add_argument("--to", choices=["pilot", "live"], help="override config mode")
    ap.add_argument("--marker", help="skip if this file exists; create it after a successful send")
    ap.add_argument("--force", action="store_true", help="ignore the marker (manual re-run)")
    ap.add_argument("--dry-run", action="store_true", help="validate everything but do not send")
    args = ap.parse_args()

    try:
        with open(HERE / "config.json", encoding="utf-8-sig") as f:
            cfg = json.load(f)
    except FileNotFoundError:
        fail("config.json not found - run: python setup.py --chat-id <your chat id> (see INSTALL.md)", 2)

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8-sig")
    elif args.message is not None:
        text = args.message
    elif not sys.stdin.isatty():
        text = sys.stdin.buffer.read().decode("utf-8-sig")
    else:
        fail("no message: use --message, --file or pipe text on stdin", 2)
    text = text.strip()
    if not text:
        fail("message is empty", 2)
    if len(text) > MAX_LEN:
        fail(f"message is {len(text)} chars, Telegram limit is {MAX_LEN}", 2)

    mode = args.to or cfg.get("mode", "pilot")
    chat_id = str(cfg.get("pilotChatId" if mode == "pilot" else "liveChatId", "")).strip()
    if not chat_id:
        fail(f"no chat id configured for mode '{mode}' in config.json", 2)

    token_var = cfg.get("tokenEnvVar", "BRIEF_BOT_TOKEN")
    token = os.environ.get(token_var, "").strip()
    if not token:
        fail(f"environment variable {token_var} is not set in this process "
             f"(after setx a full app restart is needed)", 2)

    marker = Path(args.marker) if args.marker else None
    if marker and marker.exists() and not args.force:
        log(f"SKIP already sent (marker {marker.name} exists)")
        print("ALREADY_SENT: marker exists, nothing sent (use --force to resend)")
        return

    if args.dry_run:
        print(f"DRY_RUN_OK mode={mode} chars={len(text)} token_var={token_var} (nothing sent)")
        return

    body = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    last_err = "unknown error"
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            if result.get("ok"):
                if marker:
                    marker.parent.mkdir(parents=True, exist_ok=True)
                    marker.write_text(datetime.now().isoformat(timespec="seconds"), encoding="utf-8")
                log(f"OK mode={mode} chars={len(text)}")
                print(f"SENT mode={mode} chars={len(text)}")
                return
            last_err = f"Telegram said ok=false: {result.get('description', '')}"
        except urllib.error.HTTPError as e:
            try:
                desc = json.loads(e.read().decode("utf-8")).get("description", "")
            except Exception:
                desc = ""
            hints = {
                400: "the chat id is wrong, or the person has not pressed Start on the bot",
                401: "the bot token is invalid",
                403: "the person has not pressed Start on the bot, or blocked it",
                404: "the bot token is invalid (Telegram answers 404 for a wrong token)",
            }
            last_err = f"HTTP {e.code} {desc}".strip()
            if e.code in hints:
                last_err += f" - {hints[e.code]}"
            if e.code in (400, 401, 403, 404):  # config problem, retrying won't help
                break
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = f"network error: {type(e).__name__}"
        if attempt < 3:
            time.sleep(5 * attempt)
    fail(f"send failed after retries: {last_err}")


if __name__ == "__main__":
    main()
