# WhatsApp Reminder Setup — Step by Step

No Twilio. Uses `whatsapp-web.js` — your own WhatsApp Web session, automated.

## 1. Install Node.js dependencies

```
cd whatsapp-bot
npm install
```

## 2. Set your secret API key

Copy `.env.example` to `.env` and change `WA_BOT_API_KEY` to any random string.
Then either `export` the same values before starting Flask, or hardcode the
same string in `reminder_scheduler.py` (`WA_BOT_API_KEY`).

## 3. Start the WhatsApp bot (keep this running 24x7)

```
node index.js
```

A QR code will print in the terminal. Open WhatsApp on your phone ->
Settings -> Linked Devices -> Link a Device -> scan it. Once you see
`WhatsApp client is READY` in the logs, it's live.

**Important:** this process must stay running all the time (use `pm2`,
`screen`, `tmux`, or a systemd service) — if it stops, the 10:30 AM job
and the dashboard button won't be able to send anything until it's
restarted (and if the session ever logs out, you'll need to re-scan).

## 4. Update your Flask app

- Replace your old `reminder_scheduler.py` with the new one in this folder.
- Apply the 3 small edits in `app_py_additions.py` to your `app.py`
  (add `status` field, add the import, add the `/send-reminder/<sno>` route).
- Apply the edits in `critical_pending_html_additions.txt` to
  `templates/critical_pending.html` (adds the 📱 button column).
- Fill in real phone numbers for every name in `SUPERVISOR_CONTACTS`
  inside `reminder_scheduler.py`.
- Make sure your Google Sheet's "Status" column only ever contains
  exactly `Pending` or `Completed` (case doesn't matter, the code lowercases
  it, but avoid typos like "Compelted" — those will be treated as Pending).

## 5. Install the new Python dependency

```
pip install apscheduler requests
```

(`twilio` is no longer needed — you can remove it if it was in
requirements.txt.)

## 6. Run Flask as usual

```
python app.py
```

You should see: `[reminder_scheduler] Daily 10:30 AM WhatsApp reminder job started.`

## How it behaves

- **Every day at 10:30 AM**: every row where Status = "Pending" gets a
  reminder sent to the assignee's Contact No AND the supervisor
  (from SUPERVISOR_CONTACTS, matched by "Allotted By" name).
- **When Status flips to "Completed"**: the very next time the daily job
  (or you) checks that row, it sends ONE completion message to both
  people — then remembers it in `completed_notified.json` and never
  sends that completion message again, even after restarts.
- **Dashboard 📱 button**: sends the same message immediately for that
  one row, without waiting for 10:30 AM. Uses the exact same logic, so
  it respects the one-time-completed rule too — clicking it on an
  already-notified completed task will just skip silently (marked
  `skipped: true` in the response).

## Files in this folder

- `whatsapp-bot/index.js` + `package.json` + `.env.example` — the Node
  service that actually talks to WhatsApp.
- `reminder_scheduler.py` — replaces your old Twilio-based one.
- `app_py_additions.py` — exact lines to add to your existing `app.py`.
- `critical_pending_html_additions.txt` — exact lines to add to your
  existing `critical_pending.html`.
