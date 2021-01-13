from django.urls import path

from . import views


app_name = 'talents'

urlpatterns = [
    path('', views.TalentListAPIView.as_view(), name='list'),
    path('<int:talent_id>/', views.RetrieveTalentAPIView.as_view(), name='retrieve'),
    path(
        '<int:talent_id>/shoutouts/',
        views.TalentShoutoutListAPIView.as_view(),
        name='shoutouts'
    ),
    path('update/', views.RetrieveUpdateTalentAPIView.as_view(), name='update'),
    path('enroll/', views.EnrollAPIView.as_view(), name='enroll'),
]
