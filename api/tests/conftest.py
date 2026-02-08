import pytest
from django.contrib.auth.models import User

from app.core.models import FoodPreferences, PrefMenu, Profile, UserMenu
from app.food.models import Food, FoodIndex
from app.plan.models import FoodAmount, Meal, PlanMeal


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="test@example.com",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def profile(user):
    return Profile.objects.create(
        user=user,
        sex="male",
        age=30,
        weight=180,
        height_feet=5,
        height_inches=10,
        activity=2,
    )


@pytest.fixture
def sample_food(db):
    return Food.objects.create(
        food_description="Chicken Breast, grilled",
        calories=165,
        protein_g=31.0,
        fat_g=3.6,
        carb_g=0,
        saturated_fat_g=1.0,
        fiber_g=0,
        sugar_g=0,
        sodium_mg=74,
        cholesterol_mg=85,
        calcium_mg=15,
        iron_mg=1.0,
        vit_a_mcg=6,
        vit_c_mg=0,
        serving_size_val=100,
        food_type_grp="grocery",
        default_dish_num="Main Courses",
    )


@pytest.fixture
def sample_foods(db):
    """Create a small set of foods for testing."""
    foods_data = [
        ("Chicken Breast", 165, 31.0, 3.6, 0, "Main Courses"),
        ("Brown Rice", 123, 2.7, 1.0, 25.6, "Sides"),
        ("Broccoli", 55, 3.7, 0.6, 11.2, "Sides"),
        ("Greek Yogurt", 100, 17.0, 0.7, 6.0, "Whole Meals"),
        ("Oatmeal", 154, 5.4, 2.6, 27.4, "Whole Meals"),
        ("Almonds", 164, 6.0, 14.2, 6.1, "Whole Meals"),
        ("Salmon", 208, 20.0, 13.0, 0, "Main Courses"),
        ("Sweet Potato", 103, 2.3, 0.1, 24.0, "Sides"),
    ]
    foods = []
    for desc, cal, pro, fat, carb, dish in foods_data:
        food = Food.objects.create(
            food_description=desc,
            calories=cal,
            protein_g=pro,
            fat_g=fat,
            carb_g=carb,
            saturated_fat_g=0,
            fiber_g=2,
            sugar_g=1,
            sodium_mg=50,
            cholesterol_mg=10,
            calcium_mg=20,
            iron_mg=1,
            vit_a_mcg=10,
            vit_c_mg=5,
            serving_size_val=100,
            food_type_grp="grocery",
            default_dish_num=dish,
            max_servings=3,
            max_num_per_week=3,
        )
        foods.append(food)
        FoodIndex.objects.create(
            food=food,
            pro_index=round(pro / max(cal, 1), 4),
            fat_index=round(fat / max(cal, 1), 4),
            car_index=round(carb / max(cal, 1), 4),
        )
    return foods


@pytest.fixture
def user_with_menus(user, profile, sample_foods):
    """Create a user with PrefMenus and FoodPreferences."""
    br_pref = PrefMenu.objects.create(
        user=user, default_flg=True, meal_type="Breakfast"
    )
    lu_pref = PrefMenu.objects.create(
        user=user, default_flg=True, meal_type="Lunch"
    )
    di_pref = PrefMenu.objects.create(
        user=user, default_flg=True, meal_type="Dinner"
    )
    sn_pref = PrefMenu.objects.create(
        user=user, default_flg=True, meal_type="Snack"
    )

    UserMenu.objects.create(
        user=user,
        breakfast_prefmenu=br_pref,
        lunch_prefmenu=lu_pref,
        dinner_prefmenu=di_pref,
        snack_prefmenu=sn_pref,
    )

    # Assign foods: breakfast gets Whole Meals, lunch/dinner get Main Courses + Sides
    for food in sample_foods:
        dish = food.default_dish_num
        if dish == "Whole Meals":
            FoodPreferences.objects.create(
                meal_type="Breakfast", prefmenu=br_pref, dish_num=dish, food=food
            )
            FoodPreferences.objects.create(
                meal_type="Snack", prefmenu=sn_pref, dish_num=dish, food=food
            )
        else:
            FoodPreferences.objects.create(
                meal_type="Lunch", prefmenu=lu_pref, dish_num=dish, food=food
            )
            FoodPreferences.objects.create(
                meal_type="Dinner", prefmenu=di_pref, dish_num=dish, food=food
            )

    return user, {
        "br": br_pref,
        "lu": lu_pref,
        "di": di_pref,
        "sn": sn_pref,
    }
