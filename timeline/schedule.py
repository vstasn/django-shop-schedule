from django.conf import settings
import calendar
from datetime import timedelta
from .utils import tdeltatostr, strtotime, next_weekday


def get_default_schedule():
    calendar_ = calendar.Calendar(firstweekday=0)
    default_schedule = {}

    for weekday in calendar_.iterweekdays():
        dayScheduler = DayScheduler(weekday)
        default_schedule[weekday] = dayScheduler.create(settings.DEFAULT_SHOP_SCHEDULE)

    return default_schedule


class DayScheduler:
    def __init__(self, weekday, *args, **kwargs):
        self.weekday = weekday
        self.end_of_the_day = timedelta(hours=23, minutes=59)
        self.start_of_the_day = timedelta(hours=0, minutes=0)
        return super().__init__(*args, **kwargs)

    def check_if_finish_time_is_next_day(self, from_time, to_time):
        if to_time < from_time and from_time <= self.end_of_the_day:
            return True

        return False

    def create(self, data):
        breaks = data.get("breaks", {})

        from_time = strtotime(data.get("from_time"))
        to_time = strtotime(data.get("to_time"))

        return self._add_entry_slots(from_time, to_time, breaks)

    def _format_row(self, from_time, to_time, weekday=None):
        if weekday is None:
            weekday = self.weekday

        return [tdeltatostr(weekday, from_time), tdeltatostr(weekday, to_time)]

    def _add_entry_slots(self, from_time, to_time, breaks):
        result = []
        iter_breaks = iter(breaks)

        for key in range(0, len(breaks) + 1):
            try:
                row = next(iter_breaks)
                break_from = strtotime(row["from_time"]) - timedelta(minutes=1)
            except StopIteration:
                break_from = to_time
                row = []
            finally:
                result.append((from_time, break_from))
                if "to_time" in row:
                    from_time = strtotime(row["to_time"])

        return self._diff_entry_slots(result)

    def _diff_entry_slots(self, entries):
        extra_filter = []

        for entry in entries:
            from_time, to_time = entry

            if self.check_if_finish_time_is_next_day(from_time, to_time):
                extra_filter += self._add_next_day(from_time, to_time)
            else:
                extra_filter.append(self._format_row(from_time, to_time))

        return extra_filter

    def _add_next_day(self, from_time, to_time):
        result = []
        # if time_to more then 00:00, should separate on 2 row,
        result.append(self._format_row(from_time, self.end_of_the_day))
        # if a day is the last day of week, need to change
        result.append(
            self._format_row(self.start_of_the_day, to_time, next_weekday(self.weekday))
        )
        return result
