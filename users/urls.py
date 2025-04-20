from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import *

urlpatterns = [
    path('register/', UserRegisterView.as_view(),name='register'),
    path('login/',UserLoginView.as_view(),name='login'),
    path('logout/',UserLogoutView.as_view(),name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('get-all-users/<int:user_id>/',GetAllUsersView.as_view(),name='get-all-users'),
]