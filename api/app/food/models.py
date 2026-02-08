from django.conf import settings
from django.db import models


class FoodTag(models.Model):
    """Tag for categorizing foods (e.g. vegetarian, gluten-free)."""

    name = models.CharField(max_length=300, unique=True)

    class Meta:
        db_table = "food_foodtags"

    def __str__(self) -> str:
        return self.name


class Food(models.Model):
    """A food item with full nutritional data."""

    FOOD_TYPE_CHOICES = [
        ("restaurant", "restaurant"),
        ("grocery", "grocery"),
        ("raw ingredient", "raw ingredient"),
        ("recipe", "recipe"),
    ]
    DISH_CHOICES = [
        ("Sides", "Sides"),
        ("Main Courses", "Main Courses"),
        ("Whole Meals", "Whole Meals"),
    ]

    food_description = models.CharField(max_length=350, null=True)
    brand = models.CharField(max_length=250, null=True, blank=True)
    food_type_grp = models.CharField(
        max_length=30, choices=FOOD_TYPE_CHOICES, null=True, blank=True
    )
    source = models.CharField(max_length=50, null=True, blank=True)
    ingredients_list = models.TextField(null=True, blank=True)
    serving_size_raw = models.CharField(max_length=200, null=True, blank=True)
    serving_size_val = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    serving_size_unit = models.CharField(max_length=200, null=True, blank=True)

    # Nutrients (15 fields)
    calories = models.DecimalField(max_digits=10, decimal_places=0, null=True)
    protein_g = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    fat_g = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    saturated_fat_g = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    carb_g = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    fiber_g = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    sugar_g = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    sodium_mg = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    cholesterol_mg = models.DecimalField(max_digits=10, decimal_places=3, null=True)
    calcium_mg = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    iron_mg = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    vit_a_mcg = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    vit_c_mg = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    net_carb_g = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    net_sugar_g = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    # Display
    image_url = models.URLField(blank=True, default="")
    tags = models.ManyToManyField(FoodTag, through="FoodTagMapping", blank=True)

    # Preferences defaults
    default_dish_num = models.CharField(
        choices=DISH_CHOICES, default="Whole Meals", max_length=20
    )
    max_servings = models.FloatField(default=2)
    max_num_per_week = models.FloatField(default=2)
    star_rating = models.FloatField(default=2.5)

    # Is this food also a recipe?
    is_recipe = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_foods",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "food_foods"
        indexes = [
            models.Index(fields=["food_description"], name="food_description_idx"),
            models.Index(
                fields=["is_recipe", "created_by"], name="food_recipe_creator_idx"
            ),
        ]

    def __str__(self) -> str:
        return self.food_description or f"Food {self.pk}"


class FoodTagMapping(models.Model):
    """Through table linking foods to tags."""

    foodtag = models.ForeignKey(FoodTag, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    class Meta:
        db_table = "food_taggedfoods"

    def __str__(self) -> str:
        return f"{self.food} - {self.foodtag}"


class FoodIndex(models.Model):
    """Nutrient-per-calorie ratios for optimizer ranking."""

    food = models.OneToOneField(Food, on_delete=models.CASCADE, primary_key=True)
    pro_index = models.DecimalField(max_digits=7, decimal_places=4, null=True)
    fat_index = models.DecimalField(max_digits=7, decimal_places=4, null=True)
    car_index = models.DecimalField(max_digits=7, decimal_places=4, null=True)
    fib_index = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    clc_index = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    irn_index = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    vta_index = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    vtc_index = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    sug_index = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    stf_index = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    sod_index = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    cho_index = models.DecimalField(max_digits=10, decimal_places=4, null=True)

    class Meta:
        db_table = "food_foodindex"

    def __str__(self) -> str:
        return f"FoodIndex({self.food})"


class Recipe(models.Model):
    """A recipe linked 1:1 to a Food entry (where is_recipe=True)."""

    food = models.OneToOneField(
        Food, on_delete=models.CASCADE, primary_key=True, related_name="recipe"
    )
    description = models.TextField(null=True, blank=True)
    instructions = models.JSONField(default=list)
    cook_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    prep_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    servings = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    image_url = models.URLField(blank=True, default="")
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "food_recipes"

    def __str__(self) -> str:
        return f"Recipe({self.food})"


class RecipeFood(models.Model):
    """An ingredient in a recipe (food FK + amount + unit)."""

    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="ingredients"
    )
    ingred_food_desc = models.CharField(max_length=300)
    ingred_food = models.ForeignKey(
        Food, on_delete=models.SET_NULL, null=True, related_name="used_in_recipes"
    )
    ingred_amt = models.FloatField(default=1.0)
    ingred_serving_size_unit = models.CharField(max_length=300)

    class Meta:
        db_table = "food_recipefood"

    def __str__(self) -> str:
        return f"{self.ingred_food_desc} in {self.recipe}"
