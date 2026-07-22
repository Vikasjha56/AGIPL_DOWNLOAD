# AGIPL WhatsApp Reminder — Final Setup Guide

No Twilio. Uses your own WhatsApp via `whatsapp-web.js`.

---

## FILES IN THIS DELIVERY (all ready to paste, nothing to edit inside them
## except the 2 things marked "EDIT THIS" below)

```
app.py                          -> replaces your existing app.py
critical_pending.html           -> replaces templates/critical_pending.html
reminder_scheduler.py           -> replaces your existing reminder_scheduler.py
requirements.txt                -> replaces your existing requirements.txt
whatsapp-bot/index.js           -> new folder, the WhatsApp automation service
whatsapp-bot/package.json       -> new folder
whatsapp-bot/.env               -> new folder, already filled in, ready to use
```

---

## PART 1 — Your Flask project (app.py, templates, requirements.txt)

Just replace the files. Nothing to type for this part except reinstalling
Python packages, run this in your Flask project's terminal:

```
pip install -r requirements.txt
```

That single command installs everything Flask needs (`apscheduler` and
`requests` are already listed inside `requirements.txt` — you do NOT need
to `pip install` them separately, and `twilio` has been removed since it's
no longer used).

---

## PART 2 — The WhatsApp bot (a separate Node.js service)

This is a **different program** that must run 24x7 on a machine you
control — your own PC, or a small always-on VPS. It CANNOT run on Render
(Render can't keep a logged-in WhatsApp browser session alive).

On that machine, open a terminal and run these commands one by one:

```
cd whatsapp-bot
npm install
node index.js
```

- `cd whatsapp-bot` → go into the folder
- `npm install` → downloads the WhatsApp automation library (one-time)
- `node index.js` → starts the bot

The first time you run `node index.js`, a QR code will print right in
the terminal. Open WhatsApp on your phone → Settings → Linked Devices →
Link a Device → scan it. Once the terminal shows:

```
[whatsapp-bot] WhatsApp client is READY. Logged in and listening.
```

...it's live. Leave this terminal/process running all the time (use
`pm2 start index.js` instead of `node index.js` if you want it to
survive terminal closes and auto-restart on crashes — install pm2 with
`npm install -g pm2` first).

---

## PART 3 — EDIT THIS (only 2 things, both quick)

### 1. Supervisor phone numbers
Open `reminder_scheduler.py`, find this block near the top, and put in
real WhatsApp numbers (with country code, no spaces/dashes):

```python
SUPERVISOR_CONTACTS = {
    "Asfiya": "917987410451",
    "Abhishek Agrawal": "917987410451",
}
```
Add one line per name exactly as it appears in your sheet's "Allotted By"
column.

### 2. Where is the bot running, relative to Flask?

**Case A — Flask and whatsapp-bot on the SAME machine:** do nothing, the
default already works (`WA_BOT_URL=http://localhost:4000`).

**Case B — Flask is on Render (e.g. `agipl-download-system.onrender.com`)
and whatsapp-bot runs on your own PC/VPS:** Render needs a public address
to reach your bot. Easiest free option — run this on the SAME machine as
the bot, in a new terminal, while `node index.js` is still running:

```
npx ngrok http 4000
```

It will print a URL like `https://abcd1234.ngrok-free.app`. Then in
Render's dashboard → your service → Environment → add:

```
WA_BOT_URL = https://abcd1234.ngrok-free.app
WA_BOT_API_KEY = agipl-secret-key-2026
```

Redeploy on Render. (Note: free ngrok URLs change every restart — for a
permanent setup later, a small always-on VPS running both Flask and the
bot together is simpler long-term.)

---

## How it behaves once everything is running

- **Daily at 10:30 AM**: every task with Status = "Pending" gets a
  WhatsApp reminder sent to the assignee (Contact No column) AND their
  supervisor.
- **When Status flips to "Completed"**: one "task completed" message
  goes to both people, one time only — never repeated, even after
  restarts.
- **📱 button on each row**: sends that task's message immediately.
- **Click a slice of the pie chart**: sends reminders for every pending
  task belonging to that person, all at once.
- **Status banner at the top of the page**: shows what happened after
  every send (success / already-notified / failed with the real reason).

---

## If "Send failed" still shows

Open the browser console or the banner message — it now shows the real
reason (not just "not available"). Common causes:
- whatsapp-bot isn't running / QR not scanned yet → check that terminal
- `WA_BOT_URL` / `WA_BOT_API_KEY` don't match between Flask and the bot's
  `.env`
- if Flask is on Render, `WA_BOT_URL` isn't reachable from the internet
  (see Case B above)
