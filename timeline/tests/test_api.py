from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status
from rest_framework.authtoken.models import Token
from timeline.models import Shop, Daysoff, Entry
from timeline.views import ShopDetail
from freezegun import freeze_time
from django.test import override_settings
import json

User = get_user_model()


class BaseAPITest(APITestCase):
    client = APIClient()

    def _create_user(self):
        user = User(username='user1')
        user.set_password('pass1')
        user.save()
        return user

    def _login_user(self, user):
        token = Token.objects.create(user=user)
        self.client.force_authenticate(user=user, token=token.key)

    def _create_shop(self, owner):
        return Shop.objects.create(owner=owner)

    def _set_shop_view(self):
        view = ShopDetail()
        view.basename = 'shop'
        view.request = None
        return view


class UserAPILoginTest(BaseAPITest):

    def setUp(self):
        self.user = self._create_user()

    def test_user_login_and_create_token(self):
        response = self.client.post(
            reverse('login'),
            {'username': 'user1', 'password': 'pass1'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)


class UserAPITest(BaseAPITest):

    def test_user_register_valid(self):
        response = self.client.post(
            reverse('register'),
            {'username': 'test', 'password': 'test'}
        )

        user = User.objects.first()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(user.username, 'test')

    def test_user_register_invalid_empty_password(self):
        response = self.client.post(
            reverse('register'),
            {'username': 'test'}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ShopAPITest(BaseAPITest):

    def setUp(self):
        self.user = self._create_user()
        self._login_user(self.user)
        self.view = self._set_shop_view()

    def test_shop_can_save_POST_request(self):
        self.client.post(
            self.view.reverse_action('list'),
            {'title': 'shop1'},
        )

        self.assertEqual(Shop.objects.count(), 1)
        new_shop = Shop.objects.first()
        self.assertEqual('shop1', new_shop.title)

    def test_shop_trying_to_send_another_owner(self):
        fraud_user = User.objects.create(username='test1')
        self.client.post(
            self.view.reverse_action('list'),
            {'title': 'shop1', 'owner': fraud_user},
        )

        new_shop = Shop.objects.first()
        self.assertNotEqual(new_shop.owner, fraud_user)

    def test_shop_trying_to_update_foreign_shop(self):
        foreign_user = User.objects.create(username='test1')
        foreign_shop = Shop.objects.create(title='test', owner=foreign_user)

        response = self.client.put(
            self.view.reverse_action('detail', args=[foreign_shop.pk]),
            {'title': 'shop1'}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotEqual(foreign_shop.owner, self.user)

    def test_shop_owner_is_saved_if_user_is_authenticated(self):
        response = self.client.post(
            self.view.reverse_action('list'),
            {'title': 'shop1'}
        )

        shop = Shop.objects.first()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.user, shop.owner)

    def test_shop_trying_create_without_title(self):
        response = self.client.post(
            self.view.reverse_action('list'),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_shop_trying_create_if_send_primary_key(self):
        response = self.client.post(
            self.view.reverse_action('list'),
            {'title': 'shop1', 'id': 10}
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response.data['id'], 10)

    def test_shop_can_close_if_user_is_authenticated(self):
        shop = self._create_shop(self.user)
        response = self.client.post(
            self.view.reverse_action('close', [shop.pk]),
        )
        Daysoff.objects.filter(shop=shop).first()

        self.assertTrue(shop.is_dayoff())
        self.assertEqual(shop.pk, response.data['shop'])

    def test_shop_trying_close_with_foreing_shop(self):
        shop = self._create_shop(self.user)
        shop_foreign = Shop.objects.create(owner=self.user)
        response = self.client.post(
            self.view.reverse_action('close', [shop.pk]),
            {'shop': shop_foreign}
        )

        self.assertTrue(shop.is_dayoff())
        self.assertEqual(shop.pk, response.data['shop'])

    def test_shop_trying_close_with_invalid_params(self):
        shop = self._create_shop(self.user)
        response = self.client.post(
            self.view.reverse_action('close', [shop.pk]),
            {'from_date': 'fsffsfdsdf'}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_shop_trying_close_with_invalid_date_params(self):
        shop = self._create_shop(self.user)
        response = self.client.post(
            self.view.reverse_action('close', [shop.pk]),
            {'from_date': '2018-05-05', 'to_date': '2018-05-04'}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_shop_can_update_if_user_is_authenticated(self):
        shop = self._create_shop(self.user)
        self.client.post(
            self.view.reverse_action('update-schedule', [shop.pk]),
            {
                'day_of_week': 0,
                'from_time': '11.00',
                'to_time': '20.00',
                'breaks': json.dumps([{'from_time': '11.30', 'to_time': '12.30'}])
            }
        )

        count = Entry.objects.filter(shop=shop, day_of_week=0).count()

        self.assertEqual(count, 2)

    def test_shop_can_update_if_user_is_authenticated_without_breaks(self):
        shop = self._create_shop(self.user)
        self.client.post(
            self.view.reverse_action('update-schedule', [shop.pk]),
            {
                'day_of_week': 0,
                'from_time': '11.00',
                'to_time': '20.00',
            }
        )

        count = Entry.objects.filter(shop=shop, day_of_week=0).count()
        self.assertEqual(count, 1)


class ApiPermissionsTest(BaseAPITest):

    def setUp(self):
        self.view = self._set_shop_view()

    def test_cant_create_shop_without_token(self):
        response = self.client.post(
            self.view.reverse_action('list'),
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cant_update_shop_without_token(self):
        response = self.client.post(
            self.view.reverse_action('update-schedule', args=[1]),
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cant_close_shop_without_token(self):
        response = self.client.post(
            self.view.reverse_action('close', args=[1]),
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(TIME_ZONE='UTC')
class ShopAPIPublicTest(BaseAPITest):

    def setUp(self):
        user = self._create_user()
        self.shop = self._create_shop(user)
        self.view = self._set_shop_view()

    @freeze_time('2018-12-20 08:00:00')
    def test_can_check_shop_is_working(self):
        response = self.client.post(
            self.view.reverse_action('is-working', args=[self.shop.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('is_working', response.data)
        self.assertTrue(response.data['is_working'])

    @freeze_time('2018-12-20 03:00:00')
    def test_can_check_shop_is_working_at_night(self):
        response = self.client.post(
            self.view.reverse_action('is-working', args=[self.shop.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('is_working', response.data)
        self.assertFalse(response.data['is_working'])

    def test_testshop_try_to_get_schedule(self):
        url = self.view.reverse_action('schedule', args=[self.shop.pk])
        response = self.client.post(
            url
        )
        self.assertIn('working_hours', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
