import datetime

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

DISH_CHOICES = [
    ("Sides", "Sides"),
    ("Main Courses", "Main Courses"),
    ("Whole Meals", "Whole Meals"),
]


class Profile(models.Model):
    """
    User nutritional profile. 1:1 with User.

    Physical stats + 15 nutrients x 3 fields each (track flag, upper bound, lower bound).
    Kept flat (not normalized) because the optimizer accesses fields directly via raw SQL.
    """

    SEX_CHOICES = [("male", "male"), ("female", "female")]
    ACTIVITY_CHOICES = [(i, f"lvl{i}") for i in range(1, 6)]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )

    # Physical stats
    sex = models.CharField(
        choices=SEX_CHOICES, max_length=10, default="male", null=True
    )
    age = models.PositiveSmallIntegerField(null=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    weight_unit = models.CharField(max_length=2, default="lb", null=True)
    height_feet = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    height_inches = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    activity = models.PositiveSmallIntegerField(default=1, null=True)
    cal_adj = models.IntegerField(default=1, null=True)
    bmr = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    tdee = models.DecimalField(max_digits=6, decimal_places=2, null=True)

    # Nutrient tracking flags (which nutrients to optimize for)
    cal = models.BooleanField(default=True)
    pro = models.BooleanField(default=True)
    car = models.BooleanField(default=True)
    fat = models.BooleanField(default=True)
    stf = models.BooleanField(default=False)
    fib = models.BooleanField(default=False)
    sug = models.BooleanField(default=False)
    sod = models.BooleanField(default=False)
    cho = models.BooleanField(default=False)
    clc = models.BooleanField(default=False)
    irn = models.BooleanField(default=False)
    vta = models.BooleanField(default=False)
    vtc = models.BooleanField(default=False)
    nsu = models.BooleanField(default=False)
    nca = models.BooleanField(default=False)

    # Requirements (target/percentage values)
    cal_req = models.DecimalField(max_digits=7, decimal_places=2, default=2000)
    pro_perc = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.25, blank=True
    )
    car_perc = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.40, blank=True
    )
    fat_perc = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.35, blank=True
    )
    stf_thr = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    fib_req = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    sug_thr = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    sod_thr = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    cho_thr = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    clc_req = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True
    )
    irn_req = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    vta_req = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True
    )
    vtc_req = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    nsu_req = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True
    )
    nca_req = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )

    # Upper bounds
    cal_ub = models.DecimalField(max_digits=6, decimal_places=2, default=2100)
    pro_ub = models.DecimalField(max_digits=6, decimal_places=2, default=131)
    car_ub = models.DecimalField(max_digits=6, decimal_places=2, default=210)
    fat_ub = models.DecimalField(max_digits=6, decimal_places=2, default=82)
    stf_ub = models.DecimalField(max_digits=6, decimal_places=2, default=20)
    fib_ub = models.DecimalField(max_digits=6, decimal_places=2, default=45)
    sug_ub = models.DecimalField(max_digits=6, decimal_places=2, default=50)
    sod_ub = models.DecimalField(max_digits=6, decimal_places=2, default=2400)
    cho_ub = models.DecimalField(max_digits=6, decimal_places=2, default=1000)
    clc_ub = models.DecimalField(max_digits=7, decimal_places=2, default=2000)
    irn_ub = models.DecimalField(max_digits=6, decimal_places=2, default=45)
    vta_ub = models.DecimalField(max_digits=7, decimal_places=2, default=10000)
    vtc_ub = models.DecimalField(max_digits=6, decimal_places=2, default=2000)
    nsu_ub = models.DecimalField(max_digits=6, decimal_places=2, default=45)
    nca_ub = models.DecimalField(max_digits=6, decimal_places=2, default=165)

    # Lower bounds
    cal_lb = models.DecimalField(max_digits=6, decimal_places=2, default=1900)
    pro_lb = models.DecimalField(max_digits=6, decimal_places=2, default=119)
    car_lb = models.DecimalField(max_digits=6, decimal_places=2, default=190)
    fat_lb = models.DecimalField(max_digits=6, decimal_places=2, default=74)
    stf_lb = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    fib_lb = models.DecimalField(max_digits=6, decimal_places=2, default=25)
    sug_lb = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    sod_lb = models.DecimalField(max_digits=6, decimal_places=2, default=500)
    cho_lb = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    clc_lb = models.DecimalField(max_digits=7, decimal_places=2, default=1000)
    irn_lb = models.DecimalField(max_digits=6, decimal_places=2, default=18)
    vta_lb = models.DecimalField(max_digits=7, decimal_places=2, default=5000)
    vtc_lb = models.DecimalField(max_digits=6, decimal_places=2, default=90)
    nsu_lb = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    nca_lb = models.DecimalField(max_digits=6, decimal_places=2, default=145)

    class Meta:
        db_table = "core_profile"

    def __str__(self) -> str:
        return f"Profile({self.user})"


class PublicMenu(models.Model):
    """A curated, public menu template."""

    create_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="public_menus_created",
    )
    menu_name = models.CharField(max_length=300)
    menu_description = models.TextField(null=True, blank=True)
    image_url = models.URLField(blank=True, default="")
    total_clones = models.IntegerField(default=0)
    current_clones = models.IntegerField(default=0)
    breakfast_prefmenu = models.ForeignKey(
        "PrefMenu",
        on_delete=models.CASCADE,
        related_name="public_br_prefmenu",
        null=True,
    )
    lunch_prefmenu = models.ForeignKey(
        "PrefMenu",
        on_delete=models.CASCADE,
        related_name="public_lu_prefmenu",
        null=True,
    )
    dinner_prefmenu = models.ForeignKey(
        "PrefMenu",
        on_delete=models.CASCADE,
        related_name="public_di_prefmenu",
        null=True,
    )
    snack_prefmenu = models.ForeignKey(
        "PrefMenu",
        on_delete=models.CASCADE,
        related_name="public_sn_prefmenu",
        null=True,
    )

    class Meta:
        db_table = "core_publicmenu"

    def __str__(self) -> str:
        return self.menu_name


class UserMenu(models.Model):
    """A user's active menu (may be cloned from a PublicMenu)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_menus",
    )
    cloned_from = models.ForeignKey(
        PublicMenu, on_delete=models.SET_NULL, null=True, blank=True
    )
    clone_date = models.DateField(null=True, blank=True)
    breakfast_prefmenu = models.ForeignKey(
        "PrefMenu",
        on_delete=models.CASCADE,
        related_name="user_br_prefmenu",
        null=True,
    )
    lunch_prefmenu = models.ForeignKey(
        "PrefMenu",
        on_delete=models.CASCADE,
        related_name="user_lu_prefmenu",
        null=True,
    )
    dinner_prefmenu = models.ForeignKey(
        "PrefMenu",
        on_delete=models.CASCADE,
        related_name="user_di_prefmenu",
        null=True,
    )
    snack_prefmenu = models.ForeignKey(
        "PrefMenu",
        on_delete=models.CASCADE,
        related_name="user_sn_prefmenu",
        null=True,
    )

    class Meta:
        db_table = "core_usermenu"

    def __str__(self) -> str:
        return f"UserMenu({self.user}, {self.pk})"


class PrefMenu(models.Model):
    """Per-meal-type preference menu (breakfast/lunch/dinner/snack)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pref_menus"
    )
    default_flg = models.BooleanField(default=False)
    meal_type = models.CharField(
        choices=MEAL_TYPE_CHOICES, max_length=10, default="Any"
    )
    menu_name = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        db_table = "core_prefmenu"

    def __str__(self) -> str:
        return f"PrefMenu({self.user}, {self.meal_type})"


class FoodPreferences(models.Model):
    """Links a Food to a PrefMenu — the user's food preferences for a meal type."""

    meal_type = models.CharField(choices=MEAL_TYPE_CHOICES, max_length=10)
    prefmenu = models.ForeignKey(
        PrefMenu, on_delete=models.CASCADE, related_name="food_preferences"
    )
    dish_num = models.CharField(choices=DISH_CHOICES, default="Whole Meals", max_length=20)
    food = models.ForeignKey(Food, on_delete=models.CASCADE, null=True)

    class Meta:
        db_table = "core_foodpreferences"

    def __str__(self) -> str:
        return f"FoodPref({self.food}, {self.meal_type})"


class UserProbRejectFood(models.Model):
    """Per-user food personalization scores for the optimizer."""

    food = models.ForeignKey(
        Food, on_delete=models.CASCADE, related_name="user_prob_reject"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="food_scores"
    )
    viewed = models.IntegerField(default=0)
    removed = models.IntegerField(default=0)
    user_total_uses = models.IntegerField(default=0)
    dislike_ind = models.IntegerField(default=0)
    last_view = models.DateField(default=datetime.date(2018, 1, 1))
    last_use = models.DateField(default=datetime.date(2018, 1, 1))
    user_star_rating = models.FloatField(default=2.5)
    max_servings = models.FloatField(default=4)
    max_num_per_week = models.FloatField(default=2)
    default_dish_num = models.CharField(
        choices=DISH_CHOICES, default="Whole Meals", max_length=20
    )

    class Meta:
        db_table = "core_userprobrejectfood"
        unique_together = [("food", "user")]

    def __str__(self) -> str:
        return f"ProbReject({self.user}, {self.food})"

    @property
    def prob_r(self) -> float:
        if self.viewed == 0:
            return 0.5
        like_ratio = self.removed / self.viewed
        total_uses = 1 / min(max(self.user_total_uses - self.removed, 1), 20)
        days_since = (datetime.date.today() - self.last_use).days + 0.05
        last_use_score = 1 / days_since
        return (
            like_ratio * 0.5
            + last_use_score * 0.2
            + total_uses * 0.3
            + self.dislike_ind * 0.2
        )
