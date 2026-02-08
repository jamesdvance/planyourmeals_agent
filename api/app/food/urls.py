from django.urls import path

from . import views

app_name = "food"

urlpatterns = [
    path("search/", views.FoodSearchView.as_view(), name="food_search"),
    path("<int:pk>/", views.FoodDetailView.as_view(), name="food_detail"),
]
