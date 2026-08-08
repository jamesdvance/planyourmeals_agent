import datetime

import pytest
from django.db import IntegrityError

from app.core.models import (
    FoodPreferences,
    PrefMenu,
    UserMenu,
    UserProbRejectFood,
)
from app.food.models import Food, FoodIndex, FoodTag, FoodTagMapping, Recipe, RecipeFood
from app.plan.models import FoodAmount, Meal, PlanMeal


@pytest.mark.django_db
class TestFoodModels:
    def test_create_food(self, sample_food):
        assert sample_food.pk is not None
        assert sample_food.food_description == "Chicken Breast, grilled"
        assert sample_food.calories == 165

    def test_food_str(self, sample_food):
        assert str(sample_food) == "Chicken Breast, grilled"

    def test_food_index(self, sample_food):
        idx = FoodIndex.objects.create(
            food=sample_food,
            pro_index=0.1879,
            fat_index=0.0218,
            car_index=0,
        )
        assert idx.food == sample_food
        assert float(idx.pro_index) == pytest.approx(0.1879)

    def test_food_tag(self, sample_food):
        tag = FoodTag.objects.create(name="high-protein")
        FoodTagMapping.objects.create(foodtag=tag, food=sample_food)
        assert sample_food.tags.count() == 1
        assert sample_food.tags.first().name == "high-protein"

    def test_recipe(self, sample_food):
        recipe_food = Food.objects.create(
            food_description="Grilled Chicken Salad",
            calories=350,
            protein_g=28,
            fat_g=15,
            carb_g=20,
            is_recipe=True,
            serving_size_val=300,
        )
        recipe = Recipe.objects.create(
            food=recipe_food,
            description="Healthy salad with grilled chicken",
            instructions=["Grill chicken", "Chop veggies", "Combine"],
            cook_time_minutes=20,
            prep_time_minutes=10,
            servings=2,
        )
        RecipeFood.objects.create(
            recipe=recipe,
            ingred_food_desc="Chicken Breast",
            ingred_food=sample_food,
            ingred_amt=1.5,
            ingred_serving_size_unit="serving",
        )
        assert recipe.ingredients.count() == 1


@pytest.mark.django_db
class TestCoreModels:
    def test_create_profile(self, user, profile):
        assert profile.user == user
        assert profile.cal_ub == 2100
        assert profile.cal_lb == 1900
        assert profile.pro_ub == 131

    def test_prefmenu_and_food_preferences(self, user, sample_food):
        pref_menu = PrefMenu.objects.create(user=user, default_flg=True, meal_type="Dinner")
        fp = FoodPreferences.objects.create(
            meal_type="Dinner",
            prefmenu=pref_menu,
            dish_num="Main Courses",
            food=sample_food,
        )
        assert fp.prefmenu == pref_menu
        assert pref_menu.food_preferences.count() == 1

    def test_user_menu(self, user):
        br = PrefMenu.objects.create(user=user, meal_type="Breakfast")
        lu = PrefMenu.objects.create(user=user, meal_type="Lunch")
        di = PrefMenu.objects.create(user=user, meal_type="Dinner")
        sn = PrefMenu.objects.create(user=user, meal_type="Snack")

        user_menu = UserMenu.objects.create(
            user=user,
            breakfast_prefmenu=br,
            lunch_prefmenu=lu,
            dinner_prefmenu=di,
            snack_prefmenu=sn,
        )
        assert user_menu.breakfast_prefmenu == br

    def test_user_prob_reject_food(self, user, sample_food):
        uprj = UserProbRejectFood.objects.create(
            food=sample_food,
            user=user,
            viewed=10,
            removed=2,
            user_total_uses=8,
            user_star_rating=4.0,
        )
        assert uprj.prob_r is not None
        assert isinstance(uprj.prob_r, float)


@pytest.mark.django_db
class TestPlanModels:
    def test_create_meal(self, user, sample_food):
        meal = Meal.objects.create(user=user, mealname="Test Dinner")
        FoodAmount.objects.create(food=sample_food, meal=meal, amt=1.5)
        assert meal.food_amounts.count() == 1

    def test_plan_meal(self, user, sample_food):
        meal = Meal.objects.create(user=user, mealname="Dinner Meal")
        plan_meal = PlanMeal.objects.create(
            user=user,
            plan_date=datetime.date.today(),
            meal_type="Dinner",
            ml_cd="di",
            meal=meal,
        )
        assert plan_meal.meal == meal

    def test_unique_constraint(self, user, sample_food):
        today = datetime.date.today()
        PlanMeal.objects.create(user=user, plan_date=today, meal_type="Dinner", ml_cd="di")
        with pytest.raises(IntegrityError):
            PlanMeal.objects.create(user=user, plan_date=today, meal_type="Dinner", ml_cd="di")
