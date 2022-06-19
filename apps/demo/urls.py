from django.urls import re_path, include, path
from rest_framework import routers

from .views import UserViewSet, token_obtain_pair

router = routers.DefaultRouter()
router.register(r'user', UserViewSet)
urlpatterns = [
    path(r'', include(router.urls)),
    path('login/', token_obtain_pair),
]
