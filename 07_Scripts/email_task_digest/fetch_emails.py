#!/usr/bin/env python3
"""Fetch recent inbox messages from Gmail and Outlook over IMAP into JSON.

Credentials come from the environment:
  GMAIL_ADDRESS / GMAIL_APP_PASSWORD
  OUTLOOK_ADDRESS / OUTLOOK_APP_PASSWORD
Either pair may be absent; that mailbox is then skipped.
"""

import argparse
import email
import email.utils
import imaplib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from email.header import decode_header, make_header
from html.parser import HTMLParser

ACCOUNTS = [
    ("gmail", "imap.gmail.com", "GMAIL_ADDRESS", "GMAIL_APP_PASSWORD"),
    ("outlook", "outlook.office365.com", "OUTLOOK_ADDRESS", "OUTLOOK_APP_PASSWORD"),
]


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)

    def text(self):
        return " ".join("".join(self.parts).split())


def html_to_text(html):
    parser = _TextExtractor()
    parser.feed(html)
    return parser.text()


def decode_maybe(value):
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def body_text(message):
    plain, html = [], []
    for part in message.walk():
        if part.get_content_maintype() == "multipart":
            continue
        if part.get_filename():
            continue
        ctype = part.get_content_type()
        if ctype not in ("text/plain", "text/html"):
            continue
        payload = part.get_payload(decode=True)
        if payload is None:
            continue
        charset = part.get_content_charset() or "utf-8"
        try:
            text = payload.decode(charset, errors="replace")
        except LookupError:
            text = payload.decode("utf-8", errors="replace")
        (plain if ctype == "text/plain" else html).append(text)
    if plain:
        return "\n".join(plain)
    if html:
        return html_to_text("\n".join(html))
    return ""


def clean_body(text, max_chars):
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = text.strip()
    if len(text) > max_chars:
        text = text[:max_chars] + " […truncated]"
    return text


def fetch_account(label, host, address, password, since, unread_only, max_chars, limit):
    client = imaplib.IMAP4_SSL(host)
    try:
        client.login(address, password)
        client.select("INBOX", readonly=True)
        criteria = ["SINCE", since.strftime("%d-%b-%Y")]
        if unread_only:
            criteria.append("UNSEEN")
        status, data = client.search(None, *criteria)
        if status != "OK":
            raise RuntimeError(f"IMAP search failed for {label}: {status}")
        uids = data[0].split()[-limit:]
        messages = []
        for uid in uids:
            status, fetched = client.fetch(uid, "(RFC822)")
            if status != "OK" or not fetched or not isinstance(fetched[0], tuple):
                continue
            parsed = email.message_from_bytes(fetched[0][1])
            date = email.utils.parsedate_to_datetime(parsed.get("Date")) if parsed.get("Date") else None
            if date is not None and date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            if date is not None and date < since:
                continue
            messages.append(
                {
                    "mailbox": label,
                    "account": address,
                    "message_id": parsed.get("Message-ID", ""),
                    "date": date.isoformat() if date else "",
                    "from": decode_maybe(parsed.get("From")),
                    "to": decode_maybe(parsed.get("To")),
                    "subject": decode_maybe(parsed.get("Subject")),
                    "body": clean_body(body_text(parsed), max_chars),
                }
            )
        return messages
    finally:
        try:
            client.logout()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hours", type=int, default=24, help="lookback window in hours")
    ap.add_argument("--unread-only", action="store_true", help="only unseen messages")
    ap.add_argument("--max-body-chars", type=int, default=4000)
    ap.add_argument("--max-per-mailbox", type=int, default=100)
    ap.add_argument("--out", default="-", help="output JSON path, or - for stdout")
    args = ap.parse_args()

    since = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    messages, skipped, errors = [], [], []
    for label, host, addr_var, pw_var in ACCOUNTS:
        address, password = os.environ.get(addr_var), os.environ.get(pw_var)
        if not address or not password:
            skipped.append(label)
            continue
        try:
            messages.extend(
                fetch_account(
                    label,
                    host,
                    address,
                    password,
                    since,
                    args.unread_only,
                    args.max_body_chars,
                    args.max_per_mailbox,
                )
            )
        except Exception as exc:
            errors.append(f"{label}: {exc}")

    messages.sort(key=lambda m: m["date"])
    result = {
        "window_start": since.isoformat(),
        "window_end": datetime.now(timezone.utc).isoformat(),
        "skipped_mailboxes": skipped,
        "errors": errors,
        "count": len(messages),
        "messages": messages,
    }
    payload = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out == "-":
        print(payload)
    else:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(payload)
        print(f"{len(messages)} messages -> {args.out}", file=sys.stderr)
    return 1 if errors and not messages else 0


if __name__ == "__main__":
    sys.exit(main())
