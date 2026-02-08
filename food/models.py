from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField, HStoreField, JSONField

fd_types=(('restaurant','restaurant'), ('grocery','grocery'), ('raw ingredient','raw ingredient'), ('recipe','recipe'))
dishes = (('Sides', 'Sides'), ('Main Courses','Main Courses'),('Whole Meals','Whole Meals'))
# Create your models here.
class FoodTags(models.Model):
    name = models.CharField(max_length=300, unique=True)

class TaggedFoods(models.Model):
    foodtag = models.ForeignKey(FoodTags, on_delete=models.CASCADE)
    food = models.ForeignKey('Foods', on_delete=models.CASCADE)
    added_by= models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    # class Meta:
    #     unique_together = (("foodtag","food"))

class Restaurants(models.Model):
    restaurant = models.CharField(max_length=300)

def food_img_upload_path(instance, filename):
    return settings.MEDIA_ROOT+f"/food_images/{instance.food_key}/{filename}"

class Foods(models.Model):
    food_key = models.IntegerField(primary_key=True, unique=True)
    food_description = models.CharField(max_length=350, null=True)
    brand = models.CharField(max_length=250, null=True)
    food_type_grp = models.CharField(max_length=30, choices=fd_types, null=True) 
    source = models.CharField(max_length =50, null=True)
    ingredients_list = models.TextField(null=True)
    serving_size_raw = models.CharField(max_length=200, null=True)
    serving_size_val = models.DecimalField(max_digits= 10, decimal_places=2, null=True)
    serving_size_unit = models.CharField(max_length=200, null=True)
    calories =  models.DecimalField(max_digits=10, decimal_places=0, null=True)
    protein_g = models.DecimalField(max_digits=10,decimal_places=2, null=True)
    fat_g = models.DecimalField(max_digits=10, decimal_places= 2, null=True)
    saturated_fat_g = models.DecimalField(max_digits =10, decimal_places=2, null=True)
    carb_g =  models.DecimalField(max_digits =10, decimal_places=2, null=True)
    fiber_g = models.DecimalField(max_digits =10, decimal_places=2, null=True)
    sugar_g = models.DecimalField(max_digits =10, decimal_places=2, null=True)
    sodium_mg = models.DecimalField(max_digits =10, decimal_places=2, null=True)
    cholesterol_mg = models.DecimalField(max_digits =10, decimal_places=3, null=True)
    calcium_mg = models.DecimalField(max_digits =10, decimal_places=2, null=True)
    iron_mg = models.DecimalField(max_digits =10, decimal_places=2, null=True)
    vit_a_mcg = models.DecimalField(max_digits =10, decimal_places=2, null=True)
    vit_c_mg = models.DecimalField(max_digits =10, decimal_places=2, null=True)
    net_carb_g = models.DecimalField(max_digits =10, decimal_places=2, null=True)
    net_sugar_g = models.DecimalField(max_digits =10, decimal_places=2, null=True)
    #Image
    image_url = models.URLField(blank=True,default='https://planyourmealsmedia.s3.amazonaws.com/food/default_thumbnail.png') # should add a default image soon
    wide_image_url = models.URLField(null=True)
    # tags
    tags = models.ManyToManyField(FoodTags, through="TaggedFoods")
    restaurant = models.ForeignKey(Restaurants, null=True, on_delete=models.SET_NULL)
    default_dish_num = models.CharField(choices=dishes, default='Whole Meal', max_length=20)
    max_servings = models.FloatField(default=2)
    max_num_per_week = models.FloatField(default=2)
    star_rating = models.FloatField(default=2.5)

class RawIngredients(models.Model):
    food = models.OneToOneField(Foods, on_delete=models.CASCADE, primary_key=True, related_name="raw_ingredient")
    food_description = models.CharField(max_length=350, null=False, unique=True)
    cooked_flg = models.BooleanField(default=False)
    
    class Meta:
        unique_together = (("food_description","cooked_flg"))

class FoodIndex(models.Model):
    food = models.OneToOneField(Foods, on_delete=models.CASCADE, primary_key=True)
    pro_index=models.DecimalField(max_digits=7, decimal_places=4, null=True)#Will UPDATE in postgres
    fat_index=models.DecimalField(max_digits=7, decimal_places=4, null=True)#Will UPDATE in postgres
    car_index=models.DecimalField(max_digits=7, decimal_places=4, null=True)#Will UPDATE in postgres
    fib_index=models.DecimalField(max_digits=10, decimal_places=4, null=True)#Will UPDATE in postgres
    clc_index=models.DecimalField(max_digits=10, decimal_places=4, null=True)#Will UPDATE in postgres
    irn_index=models.DecimalField(max_digits=10, decimal_places=4, null=True)#Will UPDATE in postgres
    vta_index=models.DecimalField(max_digits=10, decimal_places=4, null=True)#Will UPDATE in postgres
    vtc_index=models.DecimalField(max_digits=10, decimal_places=4, null=True)#Will UPDATE in postgres
    sug_index=models.DecimalField(max_digits=10, decimal_places=4, null=True)#Will UPDATE in postgres
    stf_index=models.DecimalField(max_digits=10, decimal_places=4, null=True)#Will UPDATE in postgres
    sod_index=models.DecimalField(max_digits=10, decimal_places=4, null=True)#Will UPDATE in postgres
    cho_index=models.DecimalField(max_digits=10, decimal_places=4, null=True)#Will UPDATE in postgres

class AltServingSize(models.Model):
    food = models.OneToOneField(Foods,  on_delete=models.CASCADE, primary_key=True, related_name="alt_serving_size")
    serving_sizes = JSONField()

class RecipeSource(models.Model): # Primary Key created automatically
    source_name = models.CharField(max_length=200)
    is_user = models.BooleanField(default=False)
    source_url = models.URLField(max_length=200, null=True)
    source_logo_img = models.ImageField(upload_to='uploads/recipe_source_logos/',max_length=300, null=True) # Can add heights and widths later

class Recipes(models.Model):
    food= models.OneToOneField(Foods, on_delete=models.CASCADE, unique=True,primary_key=True, related_name='recipes') # recipe
    description = models.TextField(null=True, blank=True)
    instructions = ArrayField(models.TextField(), default=[]) # Instructions are arrays of text fields. 1 Per step. Should this be a 
    ingredient = models.ManyToManyField(Foods, through="RecipeFood", related_name='recipe_ingred_food') # List of dictionaries. Keys = 'Ingredient', Values = [unit,amount]. May need to insert directly from Python in seperate script
    cook_time = JSONField(null=True, blank=True) # DurationField is too complex - so storing two-integer arrays as [HH, MM] 
    recipe_yield = models.DecimalField(max_digits=10,decimal_places=2, default=1) # Can convert to float if problems
    added_by = models.ForeignKey(User, on_delete=models.SET('deleted_user'))
    source = models.ForeignKey(RecipeSource,on_delete=models.SET('deleted_source'))
    num_ingred = models.IntegerField(null=True)

class RecipeFood(models.Model):
    recipe = models.ForeignKey(Recipes,on_delete=models.CASCADE, related_name='recipe_food')
    ingred_food_desc = models.CharField(max_length=300)
    ingred_food = models.ForeignKey(Foods,on_delete=models.SET_NULL, null=True, related_name='ingred_food')
    ingred_amt = models.FloatField(default=1.0)
    ingred_serving_size_unit = models.CharField(max_length=300)

class FoodImages(models.Model):
    food = models.ForeignKey(Foods, on_delete=models.CASCADE, related_name='recipe_image')
    thumbnail_bad = models.BooleanField(default=False)
    wide_bad = models.BooleanField(default=False)
