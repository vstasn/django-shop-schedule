from django.core.exceptions import ValidationError
from django.test import TestCase
from django.contrib import auth
from timeline.models import Shop, Entry, Daysoff
from freezegun import freeze_time
import datetime

User = auth.get_user_model()


class UserModelTest(TestCase):
    """test user model"""

    def test_user_is_valid_with_username_and_password(self):
        """test: validate user data"""
        user = User(username="user1", password="11234")
        user.full_clean()

    def test_user_is_invalid_with_username(self):
        """test: validate user data without password"""
        user = User(username="user1")
        with self.assertRaises(ValidationError):
            user.full_clean()


class ShopModelTest(TestCase):
    """test shop model"""

    def test_default_title(self):
        shop = Shop()
        self.assertEqual(shop.title, "")

    def test_shop_is_related_to_user(self):
        user_ = User.objects.create()
        shop = Shop()
        shop.title = "shop1"
        shop.owner = user_
        shop.save()
        self.assertIn(shop, user_.shop_set.all())

    def test_shop_owner_is_not_optional(self):
        """test: should raise"""
        with self.assertRaises(ValidationError):
            Shop().full_clean()

    def test_shop_can_have_owners(self):
        """test: should not raise"""
        Shop(owner=User())

    def test_shop_filter_is_closed_with_daysoff(self):
        """test: check filter, should raise"""
        user_ = User.objects.create()
        shop = Shop.objects.create(owner=user_)
        # add days off from now
        Daysoff.objects.create(shop=shop, from_date="2017-01-01", to_date="2017-01-02")
        self.assertFalse(Shop.objects.get(id=shop.pk).is_dayoff())

    def test_shop_filter_is_closed_without_daysoff(self):
        """test: check filter, should raise"""
        user_ = User.objects.create()
        shop = Shop.objects.create(owner=user_)
        self.assertFalse(Shop.objects.get(id=shop.pk).is_dayoff())

    def test_shop_filter_is_closed_with_daysoff_valid(self):
        """test: check filter, should not raise"""
        user_ = User.objects.create()
        shop = Shop.objects.create(owner=user_)
        # close shop from now
        Daysoff.objects.create(shop=shop)
        is_dayoff = Shop.objects.get(id=shop.pk).is_dayoff()

        self.assertTrue(is_dayoff)

    def test_shop_default_schedule(self):
        """test: exists default schedule"""
        user_ = User.objects.create()
        shop = Shop.objects.create(owner=user_)
        count = Entry.objects.filter(shop=shop).count()

        self.assertGreater(count, 0)

    def test_shop_is_working(self):
        user_ = User.objects.create()
        shop = Shop.objects.create(owner=user_)
        Entry.objects.filter(shop=shop).count()
        # close shop
        Daysoff.objects.create(shop=shop)

        self.assertFalse(shop.is_working())

    def test_shop_is_working_at_night(self):
        user_ = User.objects.create()
        shop = Shop.objects.create(owner=user_)
        with freeze_time("2018-12-20 03:01:00"):
            self.assertFalse(shop.is_working())

    def test_shop_find_working_hours(self):
        user_ = User.objects.create()
        shop = Shop.objects.create(owner=user_)

        with freeze_time("2018-12-20 08:00:00"):
            self.assertTrue(shop.by_working_time())

    def test_shop_find_working_hours_at_break(self):
        user_ = User.objects.create()
        shop = Shop.objects.create(owner=user_)

        with freeze_time("2018-12-20 11:30:00"):
            self.assertFalse(shop.by_working_time())

    def test_shop_find_working_hours_at_noon(self):
        user_ = User.objects.create()
        shop = Shop.objects.create(owner=user_)

        with freeze_time("2018-12-20 00:00:00"):
            self.assertTrue(shop.by_working_time())

    def test_shop_find_working_hours_at_end_of_the_day(self):
        user_ = User.objects.create()
        shop = Shop.objects.create(owner=user_)

        with freeze_time("2018-12-20 23:59:00"):
            self.assertTrue(shop.by_working_time())


class EntryModelTest(TestCase):
    """test entry model"""

    def test_create_entry_without_shop(self):
        """test: should raise exceptions"""
        entry = Entry()
        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_create_entry_with_shop(self):
        """test: """
        user = User.objects.create()
        shop = Shop.objects.create(owner=user)
        Entry.objects.create(
            shop=shop, day_of_week=1, from_time=int("01100"), to_time=int("02100")
        )
        entry = Entry.objects.first()
        self.assertEqual(entry.shop, shop)


class DaysoffModelTest(TestCase):
    """test daysoff model"""

    def test_create_daysoff_without_shop(self):
        """test: should not raise exception"""
        daysoff_ = Daysoff()
        daysoff_.full_clean()

    def test_create_daysoff_with_invalid_date(self):
        """test: trying to create daysoff with invalid date"""
        daysoff_ = Daysoff()
        daysoff_.from_date = "3903203"
        with self.assertRaises(ValidationError):
            daysoff_.full_clean()

    def test_create_daysoff_with_valid_from_date(self):
        """test: set current date to from date (not default)"""
        current = datetime.datetime.now().date()
        daysoff_ = Daysoff.objects.create(from_date=current)

        self.assertEqual(current, daysoff_.from_date)

    def test_create_daysoff_with_default_from_date(self):
        """test: check if set default date"""
        current = datetime.datetime.now().date()
        daysoff_ = Daysoff.objects.create()

        self.assertEqual(current, daysoff_.from_date)

    def test_filter_is_closed_return_true(self):
        user_ = User.objects.create()
        shop = Shop.objects.create(owner=user_)

        Daysoff.objects.create(shop=shop)

        self.assertTrue(Daysoff.objects.is_closed().exists())

    def test_filter_is_closed_return_false(self):
        user_ = User.objects.create()
        shop = Shop.objects.create(owner=user_)

        Daysoff.objects.create(shop=shop, from_date="2017-01-02", to_date="2017-02-02")

        self.assertFalse(Daysoff.objects.is_closed().exists())
