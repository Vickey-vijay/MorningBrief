#!/usr/bin/env python3
"""One-time setup and health check for the Morning Brief (standard library only).

  python setup.py --chat-id 123456789       create/update config.json, then run the check
  python setup.py --chat-id 123456789 --token-env MY_TOKEN_VAR
  python setup.py --check                   verify everything is ready (never prints the token)
  python setup.py --check --send-test       ...and send one test message to Telegram

The bot token is NEVER stored by this script. Set it yourself as an environment
variable (its name is "tokenEnvVar" in config.json, default BRIEF_BOT_TOKEN).
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "config.json"
EXAMPLE = HERE / "config.example.json"
SENDER = HERE / "send_telegram.py"


def load_json(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def token_hint(var):
    if os.name == "nt":
        return (f'In PowerShell run:  setx {var} "<your bot token>"  '
                f"then fully quit and reopen the Claude app (a new terminal alone is not enough).")
    return (f'Add  export {var}="<your bot token>"  to ~/.zshrc or ~/.bashrc, '
            f"then fully quit and reopen the Claude app.")


def write_config(chat_id, token_env, mode):
    base = load_json(CONFIG) if CONFIG.exists() else load_json(EXAMPLE)
    if chat_id:
        base["liveChatId"] = chat_id
        base["mode"] = mode or "live"
    elif mode:
        base["mode"] = mode
    if token_env:
        base["tokenEnvVar"] = token_env
    CONFIG.write_text(json.dumps(base, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[ok] config.json written (mode={base['mode']}, tokenEnvVar={base['tokenEnvVar']})")


def run_sender(*extra):
    return subprocess.run([sys.executable, str(SENDER), *extra],
                          capture_output=True, text=True, timeout=120)


def check(send_test):
    problems = []

    if sys.version_info < (3, 9):
        problems.append(f"Python {sys.version_info.major}.{sys.version_info.minor} is too old, need 3.9+")
    else:
        print(f"[ok] Python {sys.version_info.major}.{sys.version_info.minor}")

    cfg = None
    if not CONFIG.exists():
        problems.append("config.json is missing - run: python setup.py --chat-id <your chat id>")
    else:
        try:
            cfg = load_json(CONFIG)
            print("[ok] config.json is valid")
        except (OSError, ValueError) as e:
            problems.append(f"config.json cannot be read: {e}")

    if cfg:
        mode = cfg.get("mode", "live")
        key = "pilotChatId" if mode == "pilot" else "liveChatId"
        if str(cfg.get(key, "")).strip():
            print(f"[ok] chat id is set for mode '{mode}'")
        else:
            problems.append(f"no chat id for mode '{mode}' - run: python setup.py --chat-id <your chat id>")

        var = cfg.get("tokenEnvVar", "BRIEF_BOT_TOKEN")
        if os.environ.get(var, "").strip():
            print(f"[ok] environment variable {var} is set")
        else:
            problems.append(f"environment variable {var} is not set in this process. {token_hint(var)}")

    if not problems:
        r = run_sender("--message", "setup check", "--dry-run")
        if r.returncode == 0:
            print(f"[ok] sender self-test: {r.stdout.strip()}")
        else:
            problems.append(f"sender self-test failed: {(r.stderr or r.stdout).strip()}")

    if not problems and send_test:
        r = run_sender("--message", "Morning Brief setup test OK - Telegram delivery works.")
        if r.returncode == 0:
            print(f"[ok] test message sent: {r.stdout.strip()} - check Telegram now")
        else:
            problems.append(f"test message failed: {(r.stderr or r.stdout).strip()}")

    if problems:
        print("\nNOT READY:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\nREADY")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chat-id", help="your Telegram numeric chat id")
    ap.add_argument("--token-env", help="name of the env var that holds the bot token")
    ap.add_argument("--mode", choices=["live", "pilot"], help="override send mode")
    ap.add_argument("--check", action="store_true", help="only run the health check")
    ap.add_argument("--send-test", action="store_true", help="with --check: also send a test message")
    args = ap.parse_args()

    if args.chat_id is not None and not re.fullmatch(r"-?\d{5,20}", args.chat_id.strip()):
        print("ERROR: chat id must be a number such as 123456789 "
              "(message @userinfobot on Telegram to get yours)", file=sys.stderr)
        return 2

    if args.chat_id or args.token_env or args.mode:
        write_config(args.chat_id.strip() if args.chat_id else None, args.token_env, args.mode)
    elif not args.check:
        ap.print_help()
        return 2

    return check(args.send_test)


if __name__ == "__main__":
    sys.exit(main())
