from django.contrib import admin

from app.plan.models import FoodAmount, Meal, PlanMeal

admin.site.register(Meal)
admin.site.register(FoodAmount)
admin.site.register(PlanMeal)
