"""
Create a test user with Profile, UserMenu, PrefMenus, and FoodPreferences
populated from seed foods.

Usage: python manage.py create_test_user
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from app.core.models import (
    FoodPreferences,
    PrefMenu,
    Profile,
    UserMenu,
)
from app.food.models import Food


class Command(BaseCommand):
    help = "Create a test user with profile, menus, and food preferences"

    def handle(self, *args, **options):
        username = "testuser@example.com"

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"User '{username}' already exists. Skipping."))
            return

        # Create user
        user = User.objects.create_user(
            username=username,
            email=username,
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

        # Create profile with default nutrient bounds
        Profile.objects.create(
            user=user,
            sex="male",
            age=30,
            weight=180,
            height_feet=5,
            height_inches=10,
            activity=2,
            cal_req=2000,
            pro_perc=0.25,
            car_perc=0.40,
            fat_perc=0.35,
            # Keep all default upper/lower bounds from model
        )

        # Create PrefMenus for each meal type
        br_pref = PrefMenu.objects.create(
            user=user, default_flg=True, meal_type="Breakfast", menu_name="Default Breakfast"
        )
        lu_pref = PrefMenu.objects.create(
            user=user, default_flg=True, meal_type="Lunch", menu_name="Default Lunch"
        )
        di_pref = PrefMenu.objects.create(
            user=user, default_flg=True, meal_type="Dinner", menu_name="Default Dinner"
        )
        sn_pref = PrefMenu.objects.create(
            user=user, default_flg=True, meal_type="Snack", menu_name="Default Snack"
        )

        # Create UserMenu linking to PrefMenus
        UserMenu.objects.create(
            user=user,
            breakfast_prefmenu=br_pref,
            lunch_prefmenu=lu_pref,
            dinner_prefmenu=di_pref,
            snack_prefmenu=sn_pref,
        )

        # Assign foods to PrefMenus
        foods = list(Food.objects.all())
        if not foods:
            self.stdout.write(
                self.style.WARNING("No foods found. Run load_seed_foods first.")
            )
            return

        # Breakfast foods: oatmeal, eggs, yogurt, banana, overnight oats, smoothie bowl, egg omelette
        breakfast_keywords = ["Oatmeal", "Eggs", "Yogurt", "Banana", "Overnight", "Smoothie", "Omelette", "Granola"]
        # Lunch foods: sandwiches, salads, bowls
        lunch_keywords = ["Sandwich", "Salad", "Bowl", "Burrito", "Hummus", "Stir-Fry"]
        # Dinner foods: chicken, salmon, beef, pork, turkey, shrimp, tuna
        dinner_keywords = ["Chicken", "Salmon", "Beef", "Pork", "Turkey Meatballs", "Shrimp", "Tuna", "Tofu"]
        # Snack foods: almonds, trail mix, protein bar, rice cake, blueberries, apple
        snack_keywords = ["Almond", "Trail", "Protein Bar", "Rice Cake", "Blueberries", "Apple"]

        # Side foods available for all non-snack meals
        side_keywords = ["Rice", "Quinoa", "Sweet Potato", "Broccoli", "Spinach", "Kale", "Beans", "Lentils", "Cauliflower", "Zucchini", "Pasta", "Bread", "Edamame"]

        def assign_foods(pref_menu, keywords, meal_type, dish="Whole Meals"):
            for food in foods:
                desc = food.food_description or ""
                if any(kw.lower() in desc.lower() for kw in keywords):
                    FoodPreferences.objects.create(
                        meal_type=meal_type,
                        prefmenu=pref_menu,
                        dish_num=dish,
                        food=food,
                    )

        def assign_sides(pref_menu, meal_type):
            for food in foods:
                desc = food.food_description or ""
                if any(kw.lower() in desc.lower() for kw in side_keywords):
                    FoodPreferences.objects.create(
                        meal_type=meal_type,
                        prefmenu=pref_menu,
                        dish_num="Sides",
                        food=food,
                    )

        assign_foods(br_pref, breakfast_keywords, "Breakfast")
        assign_foods(lu_pref, lunch_keywords, "Lunch")
        assign_foods(di_pref, dinner_keywords, "Dinner", "Main Courses")
        assign_foods(sn_pref, snack_keywords, "Snack")

        # Add sides to lunch and dinner
        assign_sides(lu_pref, "Lunch")
        assign_sides(di_pref, "Dinner")

        br_count = FoodPreferences.objects.filter(prefmenu=br_pref).count()
        lu_count = FoodPreferences.objects.filter(prefmenu=lu_pref).count()
        di_count = FoodPreferences.objects.filter(prefmenu=di_pref).count()
        sn_count = FoodPreferences.objects.filter(prefmenu=sn_pref).count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Created test user '{username}' with preferences: "
                f"breakfast={br_count}, lunch={lu_count}, dinner={di_count}, snack={sn_count}"
            )
        )
