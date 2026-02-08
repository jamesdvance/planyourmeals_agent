from rest_framework import serializers

from app.food.models import Food


class FoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Food
        fields = [
            "id",
            "food_description",
            "brand",
            "calories",
            "protein_g",
            "fat_g",
            "carb_g",
            "saturated_fat_g",
            "fiber_g",
            "sugar_g",
            "sodium_mg",
            "cholesterol_mg",
            "calcium_mg",
            "iron_mg",
            "vit_a_mcg",
            "vit_c_mg",
            "serving_size_val",
            "serving_size_unit",
            "image_url",
            "default_dish_num",
            "max_servings",
            "is_recipe",
        ]


class FoodSearchSerializer(serializers.Serializer):
    q = serializers.CharField(max_length=200)
