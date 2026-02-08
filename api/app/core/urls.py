from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/nutrients/", views.NutrientUpdateView.as_view(), name="nutrients"),
]
