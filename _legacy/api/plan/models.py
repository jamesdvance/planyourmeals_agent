from django.db import models
from django.contrib.auth.models import User
from food.models import Foods 
import datetime

# Model Choices
Meals = (
	('Breakfast', 'Breakfast'),
	('Lunch', 'Lunch'),
	('Dinner','Dinner'),
    ('Snack', 'Snack'),
    )
MealCodes = (
	('br', 'br'),
	('lu', 'lu'),
	('di','di'),
    ('sn', 'sn'),
    )
Food_Type_Grps = (
    ('Restaurant','restaurant'),
    ('Grocery','grocery'),
    ('Recipe','recipe'),
    ('Raw Ingredient','raw ingredient'),
    ('Mixed','mixed')
	)
Prep_Times = (
	('long', 'long'),
	('short', 'short'),
	('none', 'none'),
	)
Meal_Types = (
	('Breakfast', 'Breakfast'),
	('Lunch', 'Lunch'),
	('Dinner','Dinner'),
	('Snack', 'Snack'),
	('Any', 'Any'),
    )

# Create your models here.
class Meal(models.Model):
    user=models.ForeignKey(User, unique=False, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    mealname=models.CharField(max_length=300, default="Unnamed")
    prep_time=models.CharField(choices=Prep_Times,max_length=300, null=True, blank=True)
    food=models.ManyToManyField(Foods, through="Food_Amount")
    meal_type = models.CharField(choices=Meal_Types, max_length=300, default='Any')
    food_type_grp = models.CharField(choices=Food_Type_Grps, max_length=300, default='Mixed')
    saved = models.BooleanField(default=0)
    cloned_n = models.IntegerField(default=1)
    tags = models.ManyToManyField("MealTags", through="TaggedMeals")

class Food_Amount(models.Model):
    food=models.ForeignKey(Foods, on_delete=models.CASCADE, related_name='amount')
    meal=models.ForeignKey(Meal, on_delete=models.CASCADE)
    amt=models.DecimalField(max_digits=6, decimal_places=2,default=1) # shortened to match redux state
    serving_size_idx = models.IntegerField(default=0) # shortened to match redux state
    amount_divisor = models.FloatField(null=True) # for use in solve query

class PlanMeal(models.Model): # Formerly "WeekPlan"
    user = models.ForeignKey(User,unique=False,on_delete=models.CASCADE)
    plan_date = models.DateField(default='2019-01-01')
    ml_cd = models.CharField(choices=MealCodes, max_length=2, default='di')
    meal_type = models.CharField(choices=Meals, max_length=20, default="Dinner")
    meal = models.ForeignKey(Meal, null=True, on_delete = models.SET_NULL,blank=True)
    meal_source =  models.ForeignKey(Meal, null=True, on_delete = models.SET_NULL,blank=True, related_name="meal_source")

    class Meta:
        unique_together = (("user", "meal_type", "plan_date"))

class MealTags(models.Model):
    name = models.CharField(max_length=300, unique=True)

class TaggedMeals(models.Model):
    mealtag = models.ForeignKey(MealTags, on_delete=models.CASCADE)
    meal = models.ForeignKey('Meal', on_delete=models.CASCADE)
    added_by= models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        unique_together = (("mealtag","meal"))

class EmailLeads(models.Model):
    email = models.EmailField(max_length=200)
    source = models.CharField(max_length=200, null=True)

class MostRecentModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    opt_model = models.BinaryField(null=True)

class PodcastEpisodes(models.Model):
    episode_title = models.CharField(max_length=300, null=True)
    embed_link = models.TextField()
    episode_number = models.IntegerField()
