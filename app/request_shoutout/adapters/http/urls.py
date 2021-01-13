from django.urls import path

from . import views


app_name = 'request_shoutout'

urlpatterns = [
    path('charge/', views.ChargeOrderAPIView.as_view(), name='charge'),
    path('fulfill/', views.FulfillShoutoutRequestAPIView.as_view(), name='fulfill'),
]
