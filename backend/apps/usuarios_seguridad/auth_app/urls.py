from django.urls import path
from .views import (
    CustomLoginView,
    CustomTokenRefreshView,
    UserProfileView,
    LogoutView,
)

app_name = 'auth_app'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('me/', UserProfileView.as_view(), name='user_profile'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
