"""
Generates an official-looking PNG table image of the Critical Pending
Task sheet — PENDING rows only (any row with Status == "Completed" is
excluded) — for daily WhatsApp broadcast to Supervisor & Director.

Uses Pillow (PIL) to draw the table, so no browser/Chrome/wkhtmltoimage
dependency is needed.

QUALITY: This keeps the exact same table structure/layout as before
(which was rendering correctly) but draws everything at SCALE x size
internally, then saves at that full resolution — so the image is
sharp and readable directly in WhatsApp preview without needing to
zoom in.
"""

import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "generated_reports")
os.makedirs(OUTPUT_DIR, exist_ok=True)

COMPANY_NAME = "AGIPL"
REPORT_TITLE = "CRITICAL PENDING TASK REPORT"

# Supersampling factor for high-resolution / sharp output.
# Higher = sharper but larger file size. 3 works well for WhatsApp.
SCALE = 1

# Same column layout as before — just wider to fit larger fonts cleanly.
COLUMNS = [
    ("sno",         "S.No.",           60),
    ("assigned_to", "Allotted To",     180),
    ("details",     "Details of Work", 380),
    ("date",        "Allotted Date",   130),
    ("allotted_by", "Allotted By",     170),
    ("days",        "Pending (Days)",  130),
    ("alert",       "Alert",           110),
]

ROW_HEIGHT = 50
HEADER_HEIGHT = 56
PADDING = 22
TITLE_BLOCK_HEIGHT = 120
FOOTER_HEIGHT = 44

COLOR_HEADER_BG = (12, 42, 84)
COLOR_HEADER_TEXT = (255, 255, 255)
COLOR_TITLE_BG = (8, 28, 58)
COLOR_TITLE_TEXT = (255, 255, 255)
COLOR_ROW_EVEN = (245, 247, 250)
COLOR_ROW_ODD = (255, 255, 255)
COLOR_BORDER = (200, 205, 212)
COLOR_TEXT = (30, 30, 30)

ALERT_COLORS = {
    "High Alert":   (229, 72, 77),
    "Medium Alert": (242, 153, 74),
    "Low Alert":    (30, 158, 99),
}


def _load_font(bold=False, size=20):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _wrap_text(draw, text, font, max_width):
    text = str(text or "")
    if not text:
        return [""]
    words = text.split()
    lines, current = [], ""
    for w in words:
        trial = (current + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_width - 12:
            current = trial
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines or [""]


def alert_level(days):
    try:
        d = int(days)
    except (TypeError, ValueError):
        d = 0
    if d >= 7:
        return "High Alert"
    if d >= 3:
        return "Medium Alert"
    return "Low Alert"


def filter_pending_only(records):
    """Keeps ONLY rows where Status is NOT 'Completed'. Anything blank,
    'Pending', or anything else other than an explicit Completed status
    is treated as pending and kept — only an exact 'Completed' status
    removes the row."""
    out = []
    for r in records:
        status = str(r.get("status", "")).strip().lower()
        if status == "completed":
            continue
        out.append(r)
    return out


def generate_pending_report_image(records):
    """
    records: list of dicts (same shape as get_cached_critical_records()
    output: sno, assigned_to, contact_no, details, date, allotted_by,
    days, alert, status)

    Returns the absolute file path of the generated high-resolution PNG.
    """
    rows = filter_pending_only(records)

    # Ensure alert is always freshly computed off `days` (safety net,
    # in case the alert field wasn't recalculated upstream)
    for r in rows:
        r["alert"] = alert_level(r.get("days", 0))

    s = SCALE

    font_title = _load_font(bold=True, size=42 * s)
    font_subtitle = _load_font(bold=True, size=40 * s)
    font_header = _load_font(bold=True, size=44 * s)
    font_cell = _load_font(bold=False, size=32 * s)
    font_footer = _load_font(bold=False, size=31 * s)

    columns_scaled = [(k, label, w * s) for k, label, w in COLUMNS]
    row_height = ROW_HEIGHT * s
    header_height = HEADER_HEIGHT * s
    padding = PADDING * s
    title_block_height = TITLE_BLOCK_HEIGHT * s
    footer_height = FOOTER_HEIGHT * s

    table_width = sum(c[2] for c in columns_scaled)
    img_width = table_width + padding * 2

    # Dummy image/draw to measure wrapped row heights first
    dummy_img = Image.new("RGB", (img_width, 100), "white")
    dummy_draw = ImageDraw.Draw(dummy_img)

    row_heights = []
    for r in rows:
        max_lines = 1
        for key, _label, width in columns_scaled:
            value = r.get(key, "")
            if key == "alert":
                value = str(value)
            lines = _wrap_text(dummy_draw, value, font_cell, width)
            max_lines = max(max_lines, len(lines))
        row_heights.append(max(row_height, 26 * s * max_lines + 16 * s))

    table_height = header_height + sum(row_heights) if rows else header_height + row_height
    img_height = title_block_height + table_height + footer_height + padding * 2

    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    # ---------- TITLE BLOCK ----------
    draw.rectangle([0, 0, img_width, title_block_height], fill=COLOR_TITLE_BG)
    draw.text((padding, 20 * s), COMPANY_NAME, font=font_title, fill=COLOR_TITLE_TEXT)
    draw.text((padding, 58 * s), REPORT_TITLE, font=font_subtitle, fill=(180, 220, 255))
    generated_on = datetime.now().strftime("%d-%b-%Y %I:%M %p")
    draw.text((padding, 86 * s), f"Generated on: {generated_on}", font=font_footer, fill=(190, 195, 205))

    total_text = f"Total Pending Tasks: {len(rows)}"
    tw = draw.textlength(total_text, font=font_subtitle)
    draw.text((img_width - padding - tw, 58 * s), total_text, font=font_subtitle, fill=(180, 220, 255))

    # ---------- TABLE HEADER ----------
    y = title_block_height + padding
    x = padding
    draw.rectangle([x, y, x + table_width, y + header_height], fill=COLOR_HEADER_BG)
    cx = x
    for _key, label, width in columns_scaled:
        draw.text((cx + 9 * s, y + (header_height - 18 * s) // 2), label, font=font_header, fill=COLOR_HEADER_TEXT)
        cx += width
    y += header_height

    # ---------- TABLE ROWS ----------
    if not rows:
        draw.rectangle([x, y, x + table_width, y + row_height], fill=COLOR_ROW_EVEN)
        draw.text((x + 13 * s, y + 13 * s), "No pending tasks — all clear.", font=font_cell, fill=COLOR_TEXT)
        y += row_height
    else:
        for i, (r, rh) in enumerate(zip(rows, row_heights)):
            bg = COLOR_ROW_EVEN if i % 2 == 0 else COLOR_ROW_ODD
            draw.rectangle([x, y, x + table_width, y + rh], fill=bg)

            cx = x
            for key, _label, width in columns_scaled:
                value = r.get(key, "")

                if key == "alert":
                    alert_val = str(value)
                    color = ALERT_COLORS.get(alert_val, (100, 100, 100))
                    pill_w = min(width - 18 * s, int(draw.textlength(alert_val, font=font_cell)) + 26 * s)
                    pill_h = 30 * s
                    py = y + (rh - pill_h) // 2
                    draw.rounded_rectangle(
                        [cx + 9 * s, py, cx + 9 * s + pill_w, py + pill_h], radius=13 * s, fill=color
                    )
                    tw2 = draw.textlength(alert_val, font=font_cell)
                    draw.text(
                        (cx + 9 * s + (pill_w - tw2) / 2, py + 5 * s),
                        alert_val, font=font_cell, fill=(255, 255, 255)
                    )
                else:
                    lines = _wrap_text(draw, value, font_cell, width)
                    ty = y + (rh - 26 * s * len(lines)) // 2
                    for line in lines:
                        draw.text((cx + 9 * s, ty), line, font=font_cell, fill=COLOR_TEXT)
                        ty += 24 * s

                cx += width

            y += rh

    # ---------- TABLE BORDER ----------
    table_top = title_block_height + padding
    draw.rectangle([x, table_top, x + table_width, y], outline=COLOR_BORDER, width=2 * s)
    cx = x
    for _key, _label, width in columns_scaled:
        draw.line([(cx, table_top), (cx, y)], fill=COLOR_BORDER, width=1 * s)
        cx += width
    draw.line([(cx, table_top), (cx, y)], fill=COLOR_BORDER, width=1 * s)

    row_y = table_top + header_height
    draw.line([(x, row_y), (x + table_width, row_y)], fill=COLOR_BORDER, width=1 * s)
    if rows:
        for rh in row_heights[:-1]:
            row_y += rh
            draw.line([(x, row_y), (x + table_width, row_y)], fill=COLOR_BORDER, width=1 * s)

    # ---------- FOOTER ----------
    footer_y = y + 12 * s
    draw.line([(padding, footer_y), (img_width - padding, footer_y)], fill=COLOR_BORDER, width=1 * s)
    draw.text(
        (padding, footer_y + 8 * s),
        "This is a system-generated report. Please do not reply to this message.",
        font=font_footer, fill=(120, 125, 130)
    )

    filename = f"critical_pending_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    file_path = os.path.join(OUTPUT_DIR, filename)
    img.save(file_path, "PNG", optimize=True)
    return file_path
    
    
    
    
    
