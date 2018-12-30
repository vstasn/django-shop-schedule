from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from timeline.schedule import schedule, add_entry_slots
import datetime


class Shop(models.Model):

    title = models.TextField()
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=False, null=False, on_delete=models.CASCADE
    )

    def is_working(self):
        """
        Combine 2 methods
        """

        if self.is_dayoff():
            return False

        if not self.by_working_time():
            return False

        return True

    def is_dayoff(self):
        """
        Find rows in daysoff table, if shop owner set daysoff breaks on some days
        """

        return self.timeline_daysoff.is_closed().exists()

    def by_working_time(self, dt=None):
        """
        Check shop is working at the moment by shop standard schedule
        """

        if dt is None:
            dt = timezone.now()

        dt_time = '{}{:02d}{:02d}'.format(dt.weekday(), dt.hour, dt.minute)

        return self.timeline_entries.find_working_time(dt_time).exists()

    def save(self, *args, **kwargs):
        is_new = True
        if self.pk:
            is_new = False

        super().save(*args, **kwargs)

        if is_new:
            self.__add_schedule()

    def update_schedule(self, day_of_week, from_time, to_time, breaks=None):
        entry = add_entry_slots(day_of_week, from_time, to_time, breaks)

        if entry is not None:
            self.timeline_entries.filter(day_of_week=day_of_week).delete()
            self.__create_entries(day_of_week, entry)
            return True

        return False

    def __add_schedule(self):
        schedule_list = schedule()

        for week, rows in schedule_list.items():
            self.__create_entries(week, rows)

    def __create_entries(self, day_of_week, rows):
        for row in rows:
            from_time, to_time = row
            Entry.objects.create(
                shop=self, day_of_week=day_of_week, from_time=from_time, to_time=to_time
            )


class EntryManager(models.Manager):

    def find_working_time(self, working_time):
        return (
            self.get_queryset()
            .filter(from_time__lte=working_time)
            .filter(to_time__gte=working_time)
        )


class Entry(models.Model):
    objects = EntryManager()
    shop = models.ForeignKey(
        'Shop', related_name='timeline_entries', on_delete=models.CASCADE
    )
    # from 0 to 6
    day_of_week = models.PositiveSmallIntegerField()
    """
        Template is DHHMM, where
        D - day of week
        HH - hours
        MM - minutes
    """
    from_time = models.PositiveIntegerField()
    to_time = models.PositiveIntegerField()

    class Meta:
        index_together = ['from_time', 'to_time']


class DaysoffManager(models.Manager):

    def is_closed(self):
        """
        Filter shops that are closed
        """
        return (
            self.get_queryset()
            .filter(from_date__lte=timezone.now())
            .filter(Q(to_date__isnull=True) | Q(to_date__gte=timezone.now()))
        )


class Daysoff(models.Model):
    objects = DaysoffManager()
    shop = models.ForeignKey(
        'Shop',
        related_name='timeline_daysoff',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    from_date = models.DateField(default=datetime.date.today)
    to_date = models.DateField(blank=True, null=True)

    class Meta:
        index_together = ['from_date', 'to_date']
