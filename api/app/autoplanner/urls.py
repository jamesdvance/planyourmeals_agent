from django.urls import path

from . import views

app_name = "autoplanner"

urlpatterns = [
    path("autoplan_week/", views.AutoplanWeekView.as_view(), name="autoplan_week"),
    path(
        "get_food_alternative/",
        views.GetFoodAlternativeView.as_view(),
        name="get_food_alternative",
    ),
]
