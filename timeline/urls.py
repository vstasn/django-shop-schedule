from rest_framework.authtoken import views as auth_views
from django.conf.urls import url
from timeline import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'shop', views.ShopDetail, basename='shop')
urlpatterns = router.urls


urlpatterns += [
    url(r'^user/register/', views.create_user, name='register'),
    url(r'^user/login/', auth_views.obtain_auth_token, name='login'),
]
