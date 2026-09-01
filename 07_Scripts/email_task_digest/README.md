# Email → tasks daily digest

Two small scripts used by the "Email → Tasks Daily Digest" Devin automation.
The automation session runs `fetch_emails.py`, decides what is a task, and mails
the result with `send_digest.py`.

## Scripts

```bash
# 1. pull the last 24h of inbox mail from Gmail + Outlook
python3 fetch_emails.py --hours 24 --out /tmp/emails.json

# 2. mail a markdown digest to yourself (Gmail SMTP)
python3 send_digest.py --subject "Task digest" --body-file /tmp/digest.md
```

`fetch_emails.py` flags: `--hours`, `--unread-only`, `--max-body-chars`,
`--max-per-mailbox`, `--out`. Output JSON records `window_start`,
`skipped_mailboxes` (missing credentials), `errors` (per-mailbox login/search
failures) and one entry per message with mailbox, from, to, subject, date and a
truncated plain-text body.

`send_digest.py` flags: `--subject`, `--body-file`, `--to` (repeatable, defaults
to `GMAIL_ADDRESS`), `--dry-run` (prints the generated HTML). It sends
multipart text + HTML, rendering headings, bullets, bold/italic/code and links.

## Credentials

Environment variables, both pairs optional (a missing pair skips that mailbox,
except Gmail is required for sending):

- `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD` — app password from
  https://myaccount.google.com/apppasswords (IMAP `imap.gmail.com:993`, SMTP
  `smtp.gmail.com:465`)
- `OUTLOOK_ADDRESS`, `OUTLOOK_APP_PASSWORD` — IMAP `outlook.office365.com:993`

## Digest shape

The session groups findings into:

1. **Explicit tasks** — someone asked for something concrete.
2. **Implicit / convertible** — no ask, but an action is clearly implied
   (unanswered question, expiring offer, unpaid invoice, scheduling ping).
3. **Prep notes** — what to have ready before doing each task.
4. **Already done / no action** — one line, so nothing looks dropped.

Each item cites the source message (sender, subject, date) and never quotes more
than needed. Deadlines and amounts are copied verbatim from the mail.
