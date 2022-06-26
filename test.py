
import requests
from icalendar import Calendar, Event, Alarm
from datetime import datetime, timedelta
import logging
import hashlib

api_base = 'https://www.rhein-lahn-kreis-abfallwirtschaft.de/abfuhr_export.php'
place = 80
street = 498
year = 2022

logging.basicConfig(level=logging.INFO)
now = datetime.now()
alarm_delta = timedelta(hours=-18)
logging.info(f"Fetching events for place {place}, street {street}..")

src_events = []
for year in range(year - 1, year + 2):
    event_count = 0
    req = requests.get(api_base, params={
        'cs': 6615,
        'file': 'ics',
        'gemeinde': place,
        'strasse': street,
        'jahr': year
    })

    src_cal = Calendar.from_ical(req.text)

    for cal_subc in src_cal.subcomponents:
        if isinstance(cal_subc, Event):
            src_events.append(cal_subc)
            event_count += 1
    logging.info(f"Fetched {event_count} events for year {year}")


cal = Calendar()
cal.add('version', '2.0')
cal.add('calscale', 'GREGORIAN')
cal.add('prodid', 'jan-di/rlk-abfuhrkalender')

for src_event in src_events:
    create_alarm = True
    summary_prefix = ""
    alarm_description = ""

    match src_event['summary']:
        case "Altpapier":
            summary_prefix = "🟦 "
            alarm_description = "Blaue Tonne rausstellen"
        case "Gelbe Tonne":
            summary_prefix = "🟨 "
            alarm_description = "Gelbe Tonne rausstellen"
        case "Restabfall":
            summary_prefix = "⬛ "
            alarm_description = "Graue Tonne rausstellen"
        case "Bioabfall":
            summary_prefix = "🟫 "
            alarm_description = "Braune Tonne rausstellen"
        case "Problemabfall":
            summary_prefix = "🟥 "
            create_alarm = False

    uid = f"{src_event['summary'].lower()}-{place}-{street}-{year}-{src_event['dtstart'].to_ical().decode('utf-8')}"
    if 'description' in src_event:
        uid += f"-{src_event['description'].lower()}"
    uid = hashlib.md5(uid.encode()).hexdigest()

    event = Event()
    for prop in ['dtstart', 'dtend', 'location', 'description']:
        if prop in src_event:
            event.add(prop, src_event[prop])
    event.add('summary', f"{summary_prefix}{src_event['summary']}")
    event.add('transp', 'TRANSPARENT')
    event.add('uid', uid)
    event.add('dtstamp', now)

    if create_alarm:
        alarm = Alarm()
        alarm.add('description', alarm_description)
        alarm.add('trigger', alarm_delta)
        alarm.add('action', 'DISPLAY')
        event.add_component(alarm)

    cal.add_component(event)

with open("better.ics", 'wb') as f:
    f.write(cal.to_ical())
    f.close()
