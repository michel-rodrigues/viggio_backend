from django.urls import path

from . import views


app_name = 'wirecard'

urlpatterns = [
    path('webhook/payment/', views.WebhookPaymentAPIView.as_view(), name='webhook_payment'),
]
