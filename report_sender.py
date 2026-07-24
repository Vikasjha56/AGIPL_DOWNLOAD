"""
Sends the daily Critical Pending Task PNG report image via WhatsApp to
Supervisor & Director ONLY. Reuses whatsapp-bot's /send-image endpoint.
Fill REPORT_RECIPIENTS below with the manually-provided numbers.
"""
import os
import requests

WA_BOT_URL = os.environ.get("WA_BOT_URL", "http://localhost:4000")
WA_BOT_API_KEY = os.environ.get("WA_BOT_API_KEY", "agipl-secret-key-2026")

# TODO: fill these in manually — country code + number, no + or spaces.
REPORT_RECIPIENTS = {
    "Supervisor": "91xxxxxxxxxx",
    "Director":   "91xxxxxxxxxx",
}

REPORT_CAPTION = "🚨 Critical Pending Task Report"


def send_report_image(file_path):
    """Sends the PNG at file_path to every number in REPORT_RECIPIENTS.
    Returns a results list: [{"who": ..., "to": ..., "ok": ..., "info": ...}, ...]"""
    results = []
    if not os.path.exists(file_path):
        return [{"who": "ALL", "to": "", "ok": False, "info": f"file not found: {file_path}"}]

    for who, number in REPORT_RECIPIENTS.items():
        if not number or "X" in number:
            results.append({"who": who, "to": number, "ok": False,
                             "info": "Number not configured — edit REPORT_RECIPIENTS in report_sender.py"})
            continue
        try:
            with open(file_path, "rb") as f:
                files = {"image": (os.path.basename(file_path), f, "image/png")}
                data = {"to": number, "caption": REPORT_CAPTION}
                resp = requests.post(
                    f"{WA_BOT_URL}/send-image",
                    files=files,
                    data=data,
                    headers={"x-api-key": WA_BOT_API_KEY},
                    timeout=30,
                )
            body = resp.json()
            ok = resp.status_code == 200 and body.get("ok")
            results.append({"who": who, "to": number, "ok": ok, "info": body})
            print(f"[report_sender] {who} ({number}): {'sent' if ok else 'FAILED'} — {body}")
        except Exception as e:
            results.append({"who": who, "to": number, "ok": False, "info": str(e)})
            print(f"[report_sender] {who} ({number}): ERROR — {e}")

    return results
