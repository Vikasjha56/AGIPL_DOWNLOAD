"""
Daily WhatsApp reminder scheduler for Critical Pending Task.

Uses the LOCAL whatsapp-bot service (whatsapp-web.js — NOT Twilio) that
must be running separately: see whatsapp-bot/index.js.

Behaviour:
  - Every day at 10:30 AM: for every row where Status == "Pending",
    sends a reminder to BOTH the assignee (Contact No) and the
    supervisor (Allotted By -> SUPERVISOR_CONTACTS).
  - When a row's Status flips to "Completed": sends ONE "task completed"
    message to both assignee and supervisor, then remembers (in
    completed_notified.json) that it already sent it, so it never sends
    that completion message again — even after the scheduler restarts.
  - The dashboard "send now" button (Flask route below) reuses the same
    send_reminder_for_row() function, so manual sends and the daily job
    behave identically.

BEFORE THIS WORKS YOU MUST:
  1. cd whatsapp-bot && npm install && node index.js
     -> scan the QR code once with WhatsApp (Linked Devices)
  2. Fill in SUPERVISOR_CONTACTS below with real numbers.
  3. Set WA_BOT_API_KEY the same in whatsapp-bot/.env and here
     (or export it as an environment variable in both places).
"""

import os
import json
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


# ==========================
# CONFIG
# ==========================

# WA_BOT_URL must point to wherever whatsapp-bot/index.js is actually running.
# If Flask and the bot run on the SAME machine, "http://localhost:4000" is correct.
# If Flask is deployed online (e.g. Render) and the bot runs on your own PC/VPS,
# this MUST be that machine's public address, e.g. "http://123.45.67.89:4000"
# — set it as an environment variable named WA_BOT_URL wherever Flask is hosted.
WA_BOT_URL = os.environ.get("WA_BOT_URL", "http://localhost:4000")
WA_BOT_API_KEY = os.environ.get("WA_BOT_API_KEY", "agipl-secret-key-2026")

# "Allotted By" names -> their WhatsApp number.
# TODO: add every supervisor name that appears in your sheet.
# Format: plain number with country code works fine, e.g. "919876543210"
SUPERVISOR_CONTACTS = {
    "Asfiya": "918962861774",
    "Abhishek Agrawal": "917987410451",
}

# Where we remember "completion message already sent for this task" so it
# is never sent twice, even across restarts of this scheduler.
NOTIFIED_STORE_PATH = os.path.join(os.path.dirname(__file__), "completed_notified.json")


# ==========================
# "ALREADY NOTIFIED" STORE
# (flat file is enough here — one row per task; swap for a DB if the
#  sheet grows very large)
# ==========================

def _load_notified():
    if not os.path.exists(NOTIFIED_STORE_PATH):
        return set()
    try:
        with open(NOTIFIED_STORE_PATH, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()


def _save_notified(notified_set):
    with open(NOTIFIED_STORE_PATH, "w") as f:
        json.dump(sorted(notified_set), f, indent=2)


def _task_key(record):
    """Stable identity for a task row. S.No. is enough since it's the
    sheet's own row identifier."""
    return str(record.get("sno", ""))


# ==========================
# SENDING
# ==========================

def send_whatsapp(to_number, message):
    """Calls the local whatsapp-bot HTTP API. Returns (ok, info)."""
    if not to_number:
        return False, "no number"
    try:
        resp = requests.post(
            f"{WA_BOT_URL}/send",
            json={"to": to_number, "message": message},
            headers={"x-api-key": WA_BOT_API_KEY},
            timeout=20,
        )
        data = resp.json()
        if resp.status_code == 200 and data.get("ok"):
            print(f"[reminder_scheduler] WhatsApp sent to {to_number}")
            return True, data
        print(f"[reminder_scheduler] WhatsApp send FAILED for {to_number}:", data)
        return False, data
    except Exception as e:
        print(f"[reminder_scheduler] WhatsApp send error for {to_number}:", e)
        return False, str(e)


def pending_message(record):
    return (
        f"⏳ Reminder: Task '{record.get('details','')}' is still PENDING "
        f"since {record.get('days',0)} day(s). Please complete it and update the status."
    )


def pending_message_for_supervisor(record):
    return (
        f"⏳ Reminder: The task '{record.get('details','')}' allotted to "
        f"{record.get('assigned_to','')} is still PENDING "
        f"({record.get('days',0)} day(s))."
    )


def completed_message(record):
    return (
        f"✅ Update: Task '{record.get('details','')}' has been marked COMPLETED. "
        f"No further action needed."
    )


def completed_message_for_supervisor(record):
    return (
        f"✅ Update: The task '{record.get('details','')}' allotted to "
        f"{record.get('assigned_to','')} has been marked COMPLETED."
    )


def send_reminder_for_row(record, notified=None, save=True):
    """Sends the right message (pending or one-time-completed) for a
    single task record. Used by BOTH the daily job and the dashboard
    'send now' button, so behaviour is always identical.

    record must have: sno, assigned_to, contact_no, details, allotted_by,
    days, status ("Pending" or "Completed").
    """
    if notified is None:
        notified = _load_notified()

    status = str(record.get("status", "")).strip().lower()
    key = _task_key(record)
    contact = (record.get("contact_no") or "").strip()
    allotted_by = record.get("allotted_by", "")
    supervisor_number = SUPERVISOR_CONTACTS.get(allotted_by)

    results = []

    if status == "completed":
        if key in notified:
            # Already told everyone once — do nothing.
            return {"skipped": True, "reason": "completion already notified", "sno": key}

        if contact:
            ok, info = send_whatsapp(contact, completed_message(record))
            results.append({"to": "assignee", "ok": ok})
        if supervisor_number:
            ok, info = send_whatsapp(supervisor_number, completed_message_for_supervisor(record))
            results.append({"to": "supervisor", "ok": ok})

        notified.add(key)
        if save:
            _save_notified(notified)
        return {"skipped": False, "status": "completed", "sno": key, "results": results}

    else:
        # Pending -> reminder every time this is called (daily job, or manual button)
        if contact:
            ok, info = send_whatsapp(contact, pending_message(record))
            results.append({"to": "assignee", "ok": ok})
        if supervisor_number:
            ok, info = send_whatsapp(supervisor_number, pending_message_for_supervisor(record))
            results.append({"to": "supervisor", "ok": ok})

        return {"skipped": False, "status": "pending", "sno": key, "results": results}


# ==========================
# DAILY JOB (10:30 AM)
# ==========================

def run_daily_reminders(get_records_fn):
    """Called once a day at 10:30 AM. Pending tasks get a fresh reminder
    every day; Completed tasks get exactly one lifetime notification."""
    try:
        records = get_records_fn()
    except Exception as e:
        print("[reminder_scheduler] could not load records:", e)
        return

    notified = _load_notified()
    for r in records:
        send_reminder_for_row(r, notified=notified, save=False)
    _save_notified(notified)
    print(f"[reminder_scheduler] Daily run complete — processed {len(records)} task(s).")


def start_scheduler(get_records_fn):
    """Starts a background job that fires every day at 10:30 AM local time."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: run_daily_reminders(get_records_fn),
        CronTrigger(hour=10, minute=30),
        id="daily_whatsapp_reminder",
    )
    scheduler.start()
    print("[reminder_scheduler] Daily 10:30 AM WhatsApp reminder job started.")
    return scheduler
