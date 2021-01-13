from django.contrib import admin
from django.urls import path, include

from .readiness_probe_views import readiness_probe


DJANGO_ADMIN_BASE_URL = 'api/admin-control-center/'


urlpatterns = [
    path(DJANGO_ADMIN_BASE_URL, admin.site.urls),
    path('api/readiness-probe/<uuid:k8s_key>/', readiness_probe),
    path('api/accounts/', include('accounts.urls')),
    path('api/categories/', include('categories.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/v/', include('shoutouts.urls')),
    path('api/request-shoutout/', include('request_shoutout.adapters.http.urls')),
    path('api/talents/', include('talents.urls')),
    path('api/wirecard/', include('wirecard.urls')),
]
