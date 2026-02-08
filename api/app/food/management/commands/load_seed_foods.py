"""
Load 50+ representative foods with realistic nutritional data.
Also creates FoodIndex records for each food.

Usage: python manage.py load_seed_foods
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from app.food.models import Food, FoodIndex, FoodTag, FoodTagMapping


# fmt: off
SEED_FOODS = [
    # (description, brand, calories, protein_g, fat_g, carb_g, sat_fat_g, fiber_g, sugar_g, sodium_mg, chol_mg, calcium_mg, iron_mg, vit_a_mcg, vit_c_mg, serving_size_val, food_type_grp, dish)
    ("Chicken Breast, grilled", None, 165, 31.0, 3.6, 0, 1.0, 0, 0, 74, 85, 15, 1.0, 6, 0, 100, "grocery", "Main Courses"),
    ("Salmon Fillet, baked", None, 208, 20.0, 13.0, 0, 3.0, 0, 0, 59, 55, 12, 0.3, 40, 0, 100, "grocery", "Main Courses"),
    ("Ground Turkey, 93% lean", None, 170, 21.0, 9.0, 0, 2.5, 0, 0, 85, 80, 20, 1.5, 0, 0, 100, "grocery", "Main Courses"),
    ("Tofu, firm", None, 144, 17.0, 8.7, 2.8, 1.3, 2.3, 0.5, 14, 0, 683, 2.7, 0, 0, 126, "grocery", "Main Courses"),
    ("Black Beans, cooked", None, 132, 8.9, 0.5, 23.7, 0.1, 8.7, 0.3, 1, 0, 46, 2.1, 0, 0, 172, "grocery", "Sides"),
    ("Lentils, cooked", None, 116, 9.0, 0.4, 20.1, 0.1, 7.9, 1.8, 2, 0, 19, 3.3, 8, 1.5, 198, "grocery", "Sides"),
    ("Quinoa, cooked", None, 120, 4.4, 1.9, 21.3, 0.2, 2.8, 0.9, 7, 0, 17, 1.5, 0, 0, 185, "grocery", "Sides"),
    ("Brown Rice, cooked", None, 123, 2.7, 1.0, 25.6, 0.2, 1.6, 0.4, 4, 0, 3, 0.6, 0, 0, 202, "grocery", "Sides"),
    ("Sweet Potato, baked", None, 103, 2.3, 0.1, 24.0, 0, 3.8, 7.4, 41, 0, 38, 0.7, 961, 19.6, 150, "grocery", "Sides"),
    ("Broccoli, steamed", None, 55, 3.7, 0.6, 11.2, 0.1, 5.1, 2.2, 64, 0, 47, 0.7, 31, 89.2, 156, "grocery", "Sides"),
    ("Spinach, raw", None, 23, 2.9, 0.4, 3.6, 0.1, 2.2, 0.4, 79, 0, 99, 2.7, 469, 28.1, 100, "grocery", "Sides"),
    ("Kale, raw", None, 35, 2.9, 0.6, 4.4, 0.1, 4.1, 0.8, 53, 0, 254, 1.6, 241, 93.4, 67, "grocery", "Sides"),
    ("Mixed Greens Salad", None, 20, 1.5, 0.2, 3.5, 0, 1.8, 0.5, 25, 0, 50, 0.8, 200, 15, 85, "grocery", "Sides"),
    ("Avocado, whole", None, 322, 4.0, 29.5, 17.1, 4.3, 13.5, 1.3, 14, 0, 24, 1.1, 14, 20, 200, "grocery", "Sides"),
    ("Banana", None, 105, 1.3, 0.4, 27.0, 0.1, 3.1, 14.4, 1, 0, 6, 0.3, 4, 10.3, 118, "grocery", "Whole Meals"),
    ("Apple, medium", None, 95, 0.5, 0.3, 25.1, 0.1, 4.4, 19.0, 2, 0, 11, 0.2, 3, 8.4, 182, "grocery", "Whole Meals"),
    ("Blueberries", None, 84, 1.1, 0.5, 21.4, 0, 3.6, 14.7, 1, 0, 9, 0.4, 3, 14.4, 148, "grocery", "Sides"),
    ("Greek Yogurt, plain", "Fage", 100, 17.0, 0.7, 6.0, 0, 0, 6.0, 56, 10, 187, 0.1, 0, 0, 170, "grocery", "Whole Meals"),
    ("Eggs, large (2)", None, 143, 12.6, 9.5, 0.7, 3.1, 0, 0.4, 142, 372, 56, 1.8, 160, 0, 100, "grocery", "Main Courses"),
    ("Oatmeal, cooked", None, 154, 5.4, 2.6, 27.4, 0.4, 4.0, 0.6, 115, 0, 21, 2.1, 0, 0, 234, "grocery", "Whole Meals"),
    ("Whole Wheat Bread (2 slices)", None, 160, 8.0, 2.0, 28.0, 0.4, 4.0, 4.0, 320, 0, 60, 1.8, 0, 0, 56, "grocery", "Sides"),
    ("Pasta, whole wheat, cooked", None, 174, 7.5, 0.8, 37.2, 0.1, 6.3, 0.6, 4, 0, 21, 1.5, 0, 0, 140, "grocery", "Sides"),
    ("Almonds (1 oz)", None, 164, 6.0, 14.2, 6.1, 1.1, 3.5, 1.2, 1, 0, 76, 1.1, 0, 0, 28, "grocery", "Whole Meals"),
    ("Peanut Butter (2 tbsp)", None, 188, 8.0, 16.0, 6.0, 3.0, 2.0, 3.0, 136, 0, 17, 0.6, 0, 0, 32, "grocery", "Sides"),
    ("Cottage Cheese, 2%", None, 92, 12.4, 2.6, 4.8, 1.6, 0, 4.8, 348, 14, 93, 0.2, 37, 0, 113, "grocery", "Sides"),
    ("Cheddar Cheese (1 oz)", None, 114, 7.1, 9.4, 0.4, 6.0, 0, 0.1, 176, 30, 204, 0.2, 75, 0, 28, "grocery", "Sides"),
    ("Milk, 2% (1 cup)", None, 122, 8.1, 4.8, 11.7, 3.1, 0, 12.3, 100, 20, 293, 0.1, 134, 0.5, 244, "grocery", "Whole Meals"),
    ("Orange Juice (1 cup)", None, 112, 1.7, 0.5, 25.8, 0.1, 0.5, 20.8, 2, 0, 27, 0.5, 25, 124, 248, "grocery", "Whole Meals"),
    ("Tuna, canned in water", None, 116, 25.5, 0.8, 0, 0.2, 0, 0, 332, 30, 10, 1.3, 20, 0, 142, "grocery", "Main Courses"),
    ("Shrimp, cooked", None, 99, 24.0, 0.3, 0.2, 0.1, 0, 0, 111, 189, 70, 0.5, 0, 0, 100, "grocery", "Main Courses"),
    ("Beef Steak, sirloin", None, 206, 26.1, 10.6, 0, 4.1, 0, 0, 54, 75, 17, 1.7, 0, 0, 100, "grocery", "Main Courses"),
    ("Pork Tenderloin", None, 143, 26.2, 3.5, 0, 1.2, 0, 0, 48, 73, 5, 1.2, 0, 0.6, 100, "grocery", "Main Courses"),
    ("Chickpeas, cooked", None, 164, 8.9, 2.6, 27.4, 0.3, 7.6, 4.8, 7, 0, 49, 2.9, 1, 1.3, 164, "grocery", "Sides"),
    ("Edamame, shelled", None, 120, 12.0, 5.0, 9.0, 0.6, 4.0, 2.0, 6, 0, 60, 2.3, 0, 9.7, 100, "grocery", "Sides"),
    ("Hummus (2 tbsp)", None, 70, 2.0, 5.0, 4.0, 0.5, 1.0, 0, 130, 0, 10, 0.5, 0, 0, 30, "grocery", "Sides"),
    ("Trail Mix (1 oz)", None, 137, 3.5, 8.8, 12.7, 1.6, 1.4, 8.5, 34, 1, 20, 0.8, 1, 0.3, 28, "grocery", "Whole Meals"),
    ("Protein Bar", "Kind", 200, 12.0, 7.0, 24.0, 2.5, 5.0, 8.0, 140, 0, 200, 4.0, 0, 0, 50, "grocery", "Whole Meals"),
    ("Granola (1/2 cup)", None, 200, 5.0, 7.0, 32.0, 1.0, 3.0, 11.0, 15, 0, 30, 2.0, 0, 0, 55, "grocery", "Whole Meals"),
    ("Rice Cake (2)", None, 70, 1.4, 0.4, 15.0, 0, 0.4, 0, 52, 0, 2, 0.1, 0, 0, 18, "grocery", "Whole Meals"),
    ("Turkey Sandwich, whole wheat", None, 320, 24.0, 8.0, 36.0, 2.0, 4.0, 6.0, 680, 45, 80, 2.5, 10, 2, 200, "grocery", "Whole Meals"),
    ("Caesar Salad with Chicken", None, 350, 28.0, 18.0, 18.0, 4.5, 3.0, 3.0, 720, 60, 150, 2.0, 300, 20, 300, "grocery", "Whole Meals"),
    ("Veggie Stir-Fry with Tofu", None, 280, 16.0, 12.0, 30.0, 1.5, 6.0, 8.0, 480, 0, 200, 3.0, 250, 40, 350, "grocery", "Whole Meals"),
    ("Grilled Chicken Burrito Bowl", None, 450, 32.0, 12.0, 52.0, 3.0, 8.0, 5.0, 650, 65, 100, 3.5, 80, 15, 400, "grocery", "Whole Meals"),
    ("Salmon with Roasted Veggies", None, 380, 28.0, 18.0, 24.0, 3.5, 6.0, 6.0, 350, 55, 80, 2.0, 500, 30, 350, "grocery", "Whole Meals"),
    ("Overnight Oats with Berries", None, 320, 12.0, 8.0, 50.0, 1.5, 7.0, 18.0, 120, 5, 200, 2.5, 10, 10, 300, "grocery", "Whole Meals"),
    ("Smoothie Bowl", None, 350, 10.0, 8.0, 62.0, 2.0, 8.0, 35.0, 80, 5, 250, 1.5, 100, 50, 400, "grocery", "Whole Meals"),
    ("Egg White Omelette with Veggies", None, 150, 20.0, 3.0, 8.0, 0.5, 2.0, 3.0, 320, 10, 60, 1.5, 200, 25, 200, "grocery", "Whole Meals"),
    ("Turkey Meatballs (4)", None, 200, 22.0, 10.0, 4.0, 3.0, 0.5, 1.0, 400, 80, 30, 1.8, 0, 0, 120, "grocery", "Main Courses"),
    ("Cauliflower Rice", None, 25, 1.9, 0.3, 5.3, 0, 2.0, 1.9, 30, 0, 22, 0.4, 0, 48.2, 100, "grocery", "Sides"),
    ("Zucchini, grilled", None, 17, 1.2, 0.3, 3.1, 0.1, 1.0, 2.5, 8, 0, 16, 0.4, 10, 17.9, 100, "grocery", "Sides"),
]
# fmt: on

SEED_TAGS = ["high-protein", "vegetarian", "low-carb", "gluten-free", "quick-prep"]

# Tag assignments by food index
TAG_ASSIGNMENTS = {
    "high-protein": [0, 1, 2, 3, 18, 28, 29, 30, 31, 36],
    "vegetarian": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27, 32, 33, 34, 35, 37, 38, 44, 45, 46, 48, 49],
    "low-carb": [0, 1, 2, 3, 9, 10, 11, 12, 18, 28, 29, 30, 31, 48, 49],
    "gluten-free": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 22, 23, 24, 25, 26, 28, 29, 30, 31, 32, 33, 48, 49],
    "quick-prep": [14, 15, 16, 17, 22, 23, 26, 27, 34, 35, 36, 37, 38],
}


class Command(BaseCommand):
    help = "Load seed foods with realistic nutritional data"

    def handle(self, *args, **options):
        if Food.objects.exists():
            self.stdout.write(self.style.WARNING("Foods already exist. Skipping."))
            return

        # Create tags
        tag_objs = {}
        for tag_name in SEED_TAGS:
            tag_objs[tag_name], _ = FoodTag.objects.get_or_create(name=tag_name)

        # Create foods
        foods = []
        for i, row in enumerate(SEED_FOODS):
            (desc, brand, cal, pro, fat_, carb, sat, fib, sug, sod, chol, calc, iron, vta, vtc, ssv, ftg, dish) = row
            food = Food.objects.create(
                food_description=desc,
                brand=brand or "",
                calories=cal,
                protein_g=pro,
                fat_g=fat_,
                carb_g=carb,
                saturated_fat_g=sat,
                fiber_g=fib,
                sugar_g=sug,
                sodium_mg=sod,
                cholesterol_mg=chol,
                calcium_mg=calc,
                iron_mg=iron,
                vit_a_mcg=vta,
                vit_c_mg=vtc,
                serving_size_val=ssv,
                food_type_grp=ftg,
                default_dish_num=dish,
                max_servings=3,
                max_num_per_week=3,
            )
            foods.append(food)

            # Create FoodIndex (nutrient per calorie ratios)
            cal_safe = max(float(cal), 1)
            FoodIndex.objects.create(
                food=food,
                pro_index=Decimal(str(round(float(pro) / cal_safe, 4))),
                fat_index=Decimal(str(round(float(fat_) / cal_safe, 4))),
                car_index=Decimal(str(round(float(carb) / cal_safe, 4))),
                fib_index=Decimal(str(round(float(fib) / cal_safe, 4))),
                clc_index=Decimal(str(round(float(calc) / cal_safe, 4))),
                irn_index=Decimal(str(round(float(iron) / cal_safe, 4))),
                vta_index=Decimal(str(round(float(vta) / cal_safe, 4))),
                vtc_index=Decimal(str(round(float(vtc) / cal_safe, 4))),
                sug_index=Decimal(str(round(float(sug) / cal_safe, 4))),
                stf_index=Decimal(str(round(float(sat) / cal_safe, 4))),
                sod_index=Decimal(str(round(float(sod) / cal_safe, 4))),
                cho_index=Decimal(str(round(float(chol) / cal_safe, 4))),
            )

        # Assign tags
        for tag_name, food_indices in TAG_ASSIGNMENTS.items():
            for idx in food_indices:
                if idx < len(foods):
                    FoodTagMapping.objects.create(
                        foodtag=tag_objs[tag_name],
                        food=foods[idx],
                    )

        self.stdout.write(
            self.style.SUCCESS(f"Created {len(foods)} foods with FoodIndex records and tags.")
        )
