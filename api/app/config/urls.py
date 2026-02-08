from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/core/", include("app.core.urls")),
    path("api/v1/food/", include("app.food.urls")),
    path("api/v1/plan/", include("app.plan.urls")),
    path("api/v1/autoplan/", include("app.autoplanner.urls")),
]
