"""
24-hour WhatsApp reminder scheduler for Critical Pending Task.

Sends a WhatsApp message to:
  1) the assignee ("Work Allotted To") — using the "Contact No" column
     that is now in the Google Sheet, and
  2) their supervisor ("Allotted By") — using the SUPERVISOR_CONTACTS
     dict below, since the sheet only has names for this column, not
     phone numbers.

BEFORE THIS WORKS YOU MUST:
  1. pip install twilio apscheduler
  2. Sign up at https://www.twilio.com, get a WhatsApp-enabled sender
     (sandbox for testing, or an approved business number for production).
  3. Fill in TWILIO_SID / TWILIO_AUTH_TOKEN / TWILIO_WHATSAPP_FROM below
     (ideally via environment variables, not hardcoded).
  4. Fill in real phone numbers in SUPERVISOR_CONTACTS — one entry per
     name that appears in your sheet's "Allotted By" column.

This is a starting scaffold — Twilio is used here because it's the most
common WhatsApp API for this kind of use case, but if you're already using
a different provider (Gupshup, official WhatsApp Business API, etc.) let
me know and I'll swap send_whatsapp() to match it.
"""

import os
from apscheduler.schedulers.background import BackgroundScheduler

try:
    from twilio.rest import Client
except ImportError:
    Client = None  # scheduler will still start; sends will just fail loudly until installed


# ==========================
# TODO: fill these in (use environment variables in production)
# ==========================
TWILIO_SID = os.environ.get("TWILIO_SID", "YOUR_TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "YOUR_TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")  # Twilio sandbox by default

# "Allotted By" names -> their WhatsApp number.
# TODO: add every supervisor name that appears in your sheet.
SUPERVISOR_CONTACTS = {
    "Asfiya": "whatsapp:+91XXXXXXXXXX",
    "Abhishek Agrawal": "whatsapp:+91XXXXXXXXXX",
}

_client = None
if Client and "YOUR_TWILIO" not in TWILIO_SID:
    _client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)


def send_whatsapp(to_number, message):
    if not to_number:
        return
    if _client is None:
        print("[reminder_scheduler] Twilio not configured — would have sent to", to_number, ":", message)
        return
    to = to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}"
    try:
        _client.messages.create(from_=TWILIO_WHATSAPP_FROM, to=to, body=message)
        print(f"[reminder_scheduler] WhatsApp sent to {to}")
    except Exception as e:
        print(f"[reminder_scheduler] WhatsApp send failed for {to}:", e)


def run_daily_reminders(get_records_fn):
    """Called once every 24 hours. Reminds the assignee and the
    supervisor about every task that is still pending."""
    try:
        records = get_records_fn()
    except Exception as e:
        print("[reminder_scheduler] could not load records:", e)
        return

    for r in records:
        days = r.get("days", 0)
        assignee = r.get("assigned_to", "")
        contact = (r.get("contact_no") or "").strip()
        allotted_by = r.get("allotted_by", "")
        details = r.get("details", "")

        if contact:
            send_whatsapp(
                contact,
                f"Reminder: '{details}' assigned to you is still pending since {days} day(s). "
                f"Please complete it and update the status.",
            )

        supervisor_number = SUPERVISOR_CONTACTS.get(allotted_by)
        if supervisor_number:
            send_whatsapp(
                supervisor_number,
                f"Reminder: The task '{details}' you allotted to {assignee} is still pending "
                f"({days} day(s)).",
            )


def start_scheduler(get_records_fn):
    """Starts a background job that fires every 24 hours.
    Change 'hours=24' to e.g. hour='10' (cron trigger) for a fixed daily time instead."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: run_daily_reminders(get_records_fn), "interval", hours=24)
    scheduler.start()
    print("[reminder_scheduler] 24-hour WhatsApp reminder job started.")
    return scheduler
