from django.contrib import admin

from app.food.models import Food, FoodIndex, FoodTag, FoodTagMapping, Recipe, RecipeFood

admin.site.register(Food)
admin.site.register(FoodTag)
admin.site.register(FoodTagMapping)
admin.site.register(FoodIndex)
admin.site.register(Recipe)
admin.site.register(RecipeFood)
