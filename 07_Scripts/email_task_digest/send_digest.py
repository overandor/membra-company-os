#!/usr/bin/env python3
"""Send a markdown digest by email through Gmail SMTP.

Credentials come from the environment: GMAIL_ADDRESS / GMAIL_APP_PASSWORD.
The recipient defaults to GMAIL_ADDRESS unless --to is given.
"""

import argparse
import os
import re
import smtplib
import sys
from email.message import EmailMessage
from html import escape

INLINE = [
    (re.compile(r"\*\*(.+?)\*\*"), r"<strong>\1</strong>"),
    (re.compile(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)"), r"<em>\1</em>"),
    (re.compile(r"`(.+?)`"), r"<code>\1</code>"),
    (re.compile(r"\[(.+?)\]\((https?://[^\s)]+)\)"), r'<a href="\2">\1</a>'),
]


def inline_html(text):
    out = escape(text)
    for pattern, replacement in INLINE:
        out = pattern.sub(replacement, out)
    return out


def markdown_to_html(markdown):
    lines, html, in_list = markdown.splitlines(), [], False

    def close_list():
        nonlocal in_list
        if in_list:
            html.append("</ul>")
            in_list = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            close_list()
            continue
        heading = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if heading:
            close_list()
            level = len(heading.group(1)) + 1
            html.append(f"<h{level}>{inline_html(heading.group(2))}</h{level}>")
            continue
        bullet = re.match(r"^[-*]\s+(.*)$", stripped)
        if bullet:
            if not in_list:
                html.append("<ul>")
                in_list = True
            html.append(f"<li>{inline_html(bullet.group(1))}</li>")
            continue
        close_list()
        html.append(f"<p>{inline_html(stripped)}</p>")
    close_list()
    body = "\n".join(html)
    return (
        "<html><body style=\"font-family:-apple-system,Segoe UI,Roboto,sans-serif;"
        "font-size:14px;line-height:1.5;color:#1a1a1a;max-width:720px\">"
        f"{body}</body></html>"
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--body-file", required=True, help="markdown file to send")
    ap.add_argument("--to", action="append", default=[], help="recipient (repeatable)")
    ap.add_argument("--dry-run", action="store_true", help="print the HTML instead of sending")
    args = ap.parse_args()

    sender = os.environ.get("GMAIL_ADDRESS")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    if not sender or not password:
        print("GMAIL_ADDRESS and GMAIL_APP_PASSWORD are required", file=sys.stderr)
        return 2

    with open(args.body_file, encoding="utf-8") as handle:
        markdown = handle.read()

    recipients = args.to or [sender]
    message = EmailMessage()
    message["Subject"] = args.subject
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message.set_content(markdown)
    message.add_alternative(markdown_to_html(markdown), subtype="html")

    if args.dry_run:
        print(message.get_payload()[1].get_payload(decode=True).decode("utf-8"))
        return 0

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, password)
        smtp.send_message(message)
    print(f"sent '{args.subject}' to {', '.join(recipients)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
