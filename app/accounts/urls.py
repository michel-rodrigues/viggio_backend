from django.urls import path
from rest_framework_simplejwt import views as jwt_views

from . import views


app_name = 'accounts'

urlpatterns = [
    path('sign-up/', views.UserCreateAPIView.as_view(), name='signup'),
    path('sign-in/', views.UserLoginAPIView.as_view(), name='signin'),
    path('change-password/', views.ChangePasswordAPIView.as_view(), name='change_password'),
    path('reset-password/', views.ResetPasswordAPIView.as_view(), name='reset_password'),
    path('token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
]
