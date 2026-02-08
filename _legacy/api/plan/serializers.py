from rest_framework import serializers
from food.models import Foods, AltServingSize
from plan.models import *

class FoodModelSerializer(serializers.ModelSerializer):
	class Meta:
		model=Foods
		fields = '__all__'


# Food Search Serializer
class FoodSearchSerializer(serializers.Serializer):
	"""
	Serializes the all food model fields along with altservingsize model fields 
	"""
	food_key = serializers.IntegerField()
	food_description = serializers.CharField()
	brand = serializers.CharField()
	food_type_grp = serializers.CharField() 
	source = serializers.CharField()
	ingredients_list = serializers.CharField() # Serializer CharField corresponds to model CharField or TextField
	serving_size_raw = serializers.CharField()
	serving_size_val = serializers.DecimalField(max_digits= 10, decimal_places=2)
	serving_size_unit = serializers.CharField()
	calories =  serializers.DecimalField(max_digits=10, decimal_places=0)
	protein_g = serializers.DecimalField(max_digits=10,decimal_places=2)
	fat_g = serializers.DecimalField(max_digits=10,decimal_places=2)
	saturated_fat_g = serializers.DecimalField(max_digits=10,decimal_places=2)
	carb_g =  serializers.DecimalField(max_digits=10,decimal_places=2)
	fiber_g = serializers.DecimalField(max_digits=10,decimal_places=2)
	sugar_g = serializers.DecimalField(max_digits=10,decimal_places=2)
	sodium_mg = serializers.DecimalField(max_digits=10,decimal_places=2)
	cholesterol_mg = serializers.DecimalField(max_digits =10, decimal_places=3)
	calcium_mg = serializers.DecimalField(max_digits=10,decimal_places=2)
	iron_mg = serializers.DecimalField(max_digits=10,decimal_places=2)
	vit_a_mcg = serializers.DecimalField(max_digits=10,decimal_places=2)
	vit_c_mg = serializers.DecimalField(max_digits=10,decimal_places=2)
	image_url = serializers.URLField()
	order = serializers.IntegerField()
	serving_sizes = serializers.JSONField()
	amt = serializers.DecimalField(max_digits= 10, decimal_places=2)
	serving_size_idx = serializers.IntegerField()

#class DayPlanSerializer(serializers.Serializer):
	"""
	Non-model serializer for join of 
	"""

# class FoodSerializer(serializers.ModelSerializer):
# 	class Meta:
# 		fields = '__all__'

class FoodAmountSerializer(serializers.ModelSerializer):
	class Meta:
		model = Food_Amount 
		fields = '__all__'
		depth = 3 # don't want all the tags and restaurant info 

class MealSerializer(serializers.ModelSerializer):
	food_amount = FoodAmountSerializer()
	class Meta:
		model = Meal 
		fields = '__all__'

class PlanMealSerializer(serializers.ModelSerializer):
	meal = MealSerializer()
	class Meta:
		model = PlanMeal 
		fields = '__all__'
		depth=4
