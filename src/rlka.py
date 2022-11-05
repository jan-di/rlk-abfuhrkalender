from datetime import datetime, timedelta
import logging
import hashlib
import re
import requests
from icalendar import Calendar, Event, Alarm
from diskcache import Cache


class RLKA():
    def __init__(self, cache: Cache):
        self.cache = cache

    def get_ical(self, place: int, street: int) -> str:
        ical = self.cache.get(f'{place}-{street}', default=None)
        if ical is None:
            ical = self.fetch_ical(place=place, street=street)
            # self.cache.set(f'{place}-{street}', ical, expire=3600)

        return ical

    def fetch_ical(self, place: int, street: int) -> str:
        api_base = 'https://www.rhein-lahn-kreis-abfallwirtschaft.de/abfuhr_export.php'
        logging.basicConfig(level=logging.INFO)
        now = datetime.now()
        alarm_delta = timedelta(hours=-18)
        logging.info(f"Fetching events for place {place}, street {street}..")
        time_regex = re.compile(r'^(\d+):(\d+)-(\d+):(\d+)\s.*$')

        src_events = []
        for year in range(now.year - 1, now.year + 2):
            req = requests.get(api_base, params={
                'cs': 6615,
                'file': 'ics',
                'gemeinde': place,
                'strasse': street,
                'jahr': year
            }, timeout=5000)

            src_cal = Calendar.from_ical(req.text)

            event_count = 0
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
            time_match = None

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
                time_match = time_regex.match(src_event['description'])

            uid = hashlib.md5(uid.encode()).hexdigest()

            event = Event()
            for prop in ['location', 'description']:
                if prop in src_event:
                    event.add(prop, src_event[prop])

            dtstart = src_event['dtstart'].dt
            dtend = src_event['dtend'].dt

            if time_match is not None:
                dtstart = datetime.combine(
                    src_event['dtstart'].dt, datetime.min.time())
                dtstart = dtstart.replace(
                    hour=int(time_match.group(1)), minute=int(time_match.group(2)))
                dtend = datetime.combine(
                    src_event['dtend'].dt - timedelta(days=1), datetime.min.time())
                dtend = dtend.replace(
                    hour=int(time_match.group(3)), minute=int(time_match.group(4)))

            event.add('dtstart', dtstart)
            event.add('dtend', dtend)
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

        return cal.to_ical().decode("utf-8")
