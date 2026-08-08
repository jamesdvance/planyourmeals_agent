from django.conf import settings
from django.db import models

from app.food.models import Food

MEAL_TYPE_CHOICES = [
    ("Breakfast", "Breakfast"),
    ("Lunch", "Lunch"),
    ("Dinner", "Dinner"),
    ("Snack", "Snack"),
    ("Any", "Any"),
]

MEAL_CODE_CHOICES = [
    ("br", "br"),
    ("lu", "lu"),
    ("di", "di"),
    ("sn", "sn"),
]


class Meal(models.Model):
    """A user's meal — a collection of foods with amounts."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="meals"
    )
    created = models.DateTimeField(auto_now_add=True)
    mealname = models.CharField(max_length=300, default="Unnamed")
    meal_type = models.CharField(choices=MEAL_TYPE_CHOICES, max_length=300, default="Any")
    food = models.ManyToManyField(Food, through="FoodAmount")
    saved = models.BooleanField(default=False)

    class Meta:
        db_table = "plan_meal"

    def __str__(self) -> str:
        return f"{self.mealname} ({self.user})"


class FoodAmount(models.Model):
    """A food in a meal with its serving amount."""

    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name="meal_amounts")
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name="food_amounts")
    amt = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    serving_size_idx = models.IntegerField(default=0)
    amount_divisor = models.FloatField(null=True)

    class Meta:
        db_table = "plan_food_amount"

    def __str__(self) -> str:
        return f"{self.food} x{self.amt} in {self.meal}"


class PlanMeal(models.Model):
    """Places a Meal in a date + meal_type slot on the user's plan."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="plan_meals"
    )
    plan_date = models.DateField()
    ml_cd = models.CharField(choices=MEAL_CODE_CHOICES, max_length=2, default="di")
    meal_type = models.CharField(choices=MEAL_TYPE_CHOICES, max_length=20, default="Dinner")
    meal = models.ForeignKey(
        Meal, null=True, on_delete=models.SET_NULL, blank=True, related_name="plan_slots"
    )

    class Meta:
        db_table = "plan_planmeal"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "plan_date", "meal_type"],
                name="unique_user_date_mealtype",
            ),
        ]

    def __str__(self) -> str:
        return f"Plan({self.user}, {self.plan_date}, {self.meal_type})"
