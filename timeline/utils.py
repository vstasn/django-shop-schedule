import re
from datetime import timedelta, datetime


def strtotime(timestring):
    timestring = re.sub("[-.:]", ":", timestring)
    timeresult = datetime.strptime(timestring, "%H:%M")
    return timedelta(hours=timeresult.hour, minutes=timeresult.minute)


def tdeltatostr(day_of_week, time):
    hours = time.seconds // 3600
    minutes = (time.seconds // 60) % 60
    return "{}{:02d}{:02d}".format(day_of_week, hours, minutes)


def timetostring(rtime):
    full_date = datetime.strptime(str(rtime).zfill(5), "%w%H%M")
    return "{:02d}.{:02d}".format(full_date.hour, full_date.minute)


def next_weekday(day_of_week):
    return 0 if day_of_week == 6 else day_of_week + 1
