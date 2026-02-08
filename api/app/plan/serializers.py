from rest_framework import serializers

from app.food.serializers import FoodSerializer
from app.plan.models import FoodAmount, Meal, PlanMeal


class FoodAmountSerializer(serializers.ModelSerializer):
    food = FoodSerializer(read_only=True)

    class Meta:
        model = FoodAmount
        fields = ["id", "food", "amt", "serving_size_idx", "amount_divisor"]


class MealSerializer(serializers.ModelSerializer):
    food_amounts = FoodAmountSerializer(many=True, read_only=True)

    class Meta:
        model = Meal
        fields = ["id", "mealname", "meal_type", "created", "food_amounts"]


class PlanMealSerializer(serializers.ModelSerializer):
    meal = MealSerializer(read_only=True)

    class Meta:
        model = PlanMeal
        fields = ["id", "plan_date", "meal_type", "ml_cd", "meal"]
