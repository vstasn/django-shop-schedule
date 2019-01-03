import datetime


def format_time(day_of_week, time):
    return "{}{:02d}{:02d}".format(day_of_week, time.hour, time.minute)


def timetostring(rtime):
    full_date = datetime.datetime.strptime(str(rtime).zfill(5), "%w%H%M")
    return "{:02d}.{:02d}".format(full_date.hour, full_date.minute)


def subminutes(time1, minutes):
    tmp_datetime = datetime.datetime.combine(datetime.date(1, 1, 1), time1)
    return (tmp_datetime - datetime.timedelta(minutes=minutes)).time()


def next_weekday(day_of_week):
    return 0 if day_of_week == 6 else day_of_week + 1
