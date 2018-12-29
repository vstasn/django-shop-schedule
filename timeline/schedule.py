from django.conf import settings
import calendar
import datetime


end_of_the_day = datetime.timedelta(hours=23, minutes=59)
start_of_the_day = datetime.timedelta(hours=0, minutes=0)


def format_timedelta(td):
    minutes, seconds = divmod(td.seconds + td.days * 86400, 60)
    hours, minutes = divmod(minutes, 60)
    return '{:02d}{:02d}'.format(hours, minutes)


def from_str_to_time(data):
    hours, minutes = map(int, data.split('.'))
    return datetime.timedelta(hours=hours, minutes=minutes)


def format_entry_time(day_of_week, time):
    return f'{day_of_week}{format_timedelta(time)}'


def format_time_for_view(str_time):
    str_time = str(str_time)
    full_date = datetime.datetime.strptime(str_time.zfill(5), '%w%H%M')
    return '{:02d}.{:02d}'.format(full_date.hour, full_date.minute)


def check_if_finish_time_is_next_day(from_time, to_time):
    if to_time < from_time and from_time <= end_of_the_day:
        return True
    else:
        return False


def week_default():
    calendar_ = calendar.Calendar(firstweekday=0)
    from_calendar = {}

    for weekday in calendar_.iterweekdays():
        from_calendar[weekday] = settings.DEFAULT_SHOP_SCHEDULE

    return from_calendar


def schedule():
    week_schedule = week_default()

    week_result = {}
    for day_of_week, data in week_schedule.items():
        week_result[day_of_week] = calc_day_schedule(
            day_of_week, data
        )

    return week_result


def calc_day_schedule(day_of_week, data):
    breaks = {}
    if 'breaks' in data:
        breaks = data['breaks']

    from_time = from_str_to_time(
        data['from_time']
    )
    to_time = from_str_to_time(
        data['to_time']
    )

    return add_entry_slots(
        day_of_week, from_time, to_time, breaks
    )


def add_entry_slots(day_of_week, from_time, to_time, breaks):
    result = []
    iter_breaks = iter(breaks)

    for key in range(0, len(breaks) + 1):
        try:
            row = next(iter_breaks)
            break_from = from_str_to_time(row['from_time']) - datetime.timedelta(minutes=1)
        except StopIteration:
            break_from = to_time
            row = []
        finally:
            result.append((from_time, break_from,))
            if 'to_time' in row:
                from_time = from_str_to_time(row['to_time'])

    return diff_entry_slots(day_of_week, result)


def diff_entry_slots(day_of_week, entries):
    extra_filter = []

    def add_extra(day_of_week, from_time, to_time):
        extra_filter.append((
            format_entry_time(day_of_week, from_time),
            format_entry_time(day_of_week, to_time),
        ))

    for entry in entries:
        from_time, to_time = entry
        if check_if_finish_time_is_next_day(from_time, to_time):
            # if time_to more then 00:00, should separate on 2 row,
            add_extra(day_of_week, from_time, end_of_the_day)
            # if a day is the last day of week, need to change
            day_of_week = 0 if day_of_week == 6 else day_of_week + 1
            add_extra(day_of_week, start_of_the_day, to_time)
        else:
            add_extra(day_of_week, from_time, to_time)

    return extra_filter
