#!/usr/bin/env python3
import csv
import io
import urllib.request
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent

CSV_URL = "https://xezer.tvstream.az/schedule.csv"
CHANNEL_ID = "XezerTV.az"
CHANNEL_NAME = "Xəzər TV"
TIMEZONE = ZoneInfo("Asia/Baku")
DAYS_AHEAD = 14

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

def fetch_csv():
    req = urllib.request.Request(
        CSV_URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/csv,text/plain,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()

    # Saytın CSV-si UTF-8 görünür. BOM olarsa da problemsiz oxunur.
    for enc in ("utf-8-sig", "utf-8"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")

def parse_rows(text):
    rows = []
    reader = csv.reader(io.StringIO(text))
    for row in reader:
        if not row or len(row) < 3:
            continue

        day = row[0].strip().lower()
        hhmm = row[1].strip()
        title = ",".join(row[2:]).strip()

        if day not in WEEKDAYS:
            continue

        try:
            h, m = map(int, hhmm.split(":"))
            if not (0 <= h <= 23 and 0 <= m <= 59):
                continue
        except Exception:
            continue

        if not title:
            continue

        rows.append((day, h, m, title))

    if not rows:
        raise RuntimeError("schedule.csv-dən heç bir proqram oxunmadı.")
    return rows

def next_date_for_weekday(start_date, weekday):
    delta = (weekday - start_date.weekday()) % 7
    return start_date + timedelta(days=delta)

def build_events(rows):
    # Hər həftəlik gün bloku üçün proqramları ayrıca saxla.
    by_day = {k: [] for k in WEEKDAYS}
    for day, h, m, title in rows:
        by_day[day].append((h, m, title))

    today = datetime.now(TIMEZONE).date()
    end_date = today + timedelta(days=DAYS_AHEAD)

    events = []

    for day_name, weekday in WEEKDAYS.items():
        day_rows = by_day[day_name]
        if not day_rows:
            continue

        anchor = next_date_for_weekday(today - timedelta(days=1), weekday)

        # 14 günlük pəncərə üçün bu həftə + növbəti həftə.
        d = anchor
        while d <= end_date:
            current_date = d
            prev_minutes = None

            for h, m, title in day_rows:
                minutes = h * 60 + m

                # Məsələn 23:00-dan sonra 00:00 gəlirsə, növbəti günə keçir.
                if prev_minutes is not None and minutes < prev_minutes:
                    current_date = current_date + timedelta(days=1)

                start = datetime.combine(current_date, time(h, m), tzinfo=TIMEZONE)
                if today - timedelta(days=1) <= start.date() <= end_date + timedelta(days=1):
                    events.append({"start": start, "title": title})

                prev_minutes = minutes

            d = d + timedelta(days=7)

    # Eyni start/title təkrarlanarsa sil.
    dedup = {}
    for e in events:
        dedup[(e["start"], e["title"])] = e
    events = sorted(dedup.values(), key=lambda x: x["start"])

    # Stop vaxtını növbəti proqramın start vaxtından hesabla.
    for i, e in enumerate(events):
        if i + 1 < len(events):
            nxt = events[i + 1]["start"]
            # Növbəti proqram çox uzaqdadırsa maksimum 6 saat ver.
            if nxt > e["start"] and nxt - e["start"] <= timedelta(hours=6):
                e["stop"] = nxt
            else:
                e["stop"] = e["start"] + timedelta(hours=1)
        else:
            e["stop"] = e["start"] + timedelta(hours=1)

    # Yalnız bu gündən etibarən saxla.
    return [
        e for e in events
        if e["stop"].date() >= today and e["start"].date() <= end_date
    ]

def xmltv_dt(dt):
    # XMLTV format: YYYYMMDDHHMMSS +0400
    return dt.strftime("%Y%m%d%H%M%S %z")

def write_xml(events, out_path="xezer.xml"):
    tv = Element("tv", {
        "generator-info-name": "Xəzər TV schedule.csv -> XMLTV",
        "source-info-url": CSV_URL,
    })

    ch = SubElement(tv, "channel", {"id": CHANNEL_ID})
    SubElement(ch, "display-name", {"lang": "az"}).text = CHANNEL_NAME
    SubElement(ch, "display-name").text = "Xezer TV"

    for e in events:
        p = SubElement(tv, "programme", {
            "start": xmltv_dt(e["start"]),
            "stop": xmltv_dt(e["stop"]),
            "channel": CHANNEL_ID,
        })
        SubElement(p, "title", {"lang": "az"}).text = e["title"]

    indent(tv, space="  ")
    ElementTree(tv).write(out_path, encoding="utf-8", xml_declaration=True)

def main():
    text = fetch_csv()
    rows = parse_rows(text)
    events = build_events(rows)
    if not events:
        raise RuntimeError("XML üçün proqram yaranmadı.")
    write_xml(events)
    print(f"{len(events)} proqram yazıldı -> xezer.xml")

if __name__ == "__main__":
    main()
