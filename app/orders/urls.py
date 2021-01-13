from django.urls import path

from . import views


app_name = 'orders'

urlpatterns = [
    path('<uuid:order_hash>/', views.OrderDetailAPIView.as_view(), name='detail'),
    path('talent/', views.TalentOrdersAPIView.as_view(), name='talent_available_orders'),
]
