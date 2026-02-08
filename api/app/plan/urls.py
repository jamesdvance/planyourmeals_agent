from django.urls import path

from . import views

app_name = "plan"

urlpatterns = [
    path("day/<str:date>/", views.DayPlanView.as_view(), name="day_plan"),
]
