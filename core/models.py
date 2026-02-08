from django.db import models
from django.contrib.auth.models import User, AbstractUser
from food.models import Foods, Restaurants, FoodTags
from plan.models import Meal, MealTags
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.postgres.fields import ArrayField, HStoreField, JSONField
from django.utils import timezone
# packages
import datetime
from decimal import *
# third party
from markdownx.models import MarkdownxField


#dishes = (('side_1', 'side_1'), ('main','main'),('side_2','side_2'),('desert','desert'), ('snack', 'snack'))
dishes = (('Sides', 'Sides'), ('Main Courses','Main Courses'),('Whole Meals','Whole Meals'))
meals = (
    ('Breakfast', 'Breakfast'),
    ('Lunch', 'Lunch'),
    ('Dinner','Dinner'),
    ('Snack', 'Snack'),
    ('Any', 'Any'),
    )

# Create your models here.
class Profile(models.Model):
    sex_choices = (('male', 'male'),('female','female'))
    lvl1=1
    lvl2=2
    lvl3=3
    lvl4=4
    lvl5=5
    act_choices = ((lvl1,'lvl1'), (lvl2, 'lvl2'),(lvl3,'lvl3'),(lvl4,'lvl4'),(lvl5,'lvl5'))
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email_confirmed = models.BooleanField(default=False)
    sex = models.CharField(choices=sex_choices, max_length=10,default='male', null=True) # for starting radio group
    age = models.PositiveSmallIntegerField(null=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2,null=True) 
    weight_unit = models.CharField(max_length=2, default='lb', null=True) #kg, lb
    height_feet = models.DecimalField(max_digits=5, decimal_places=2,null=True) #
    height_inches = models.DecimalField(max_digits=5, decimal_places=2,null=True) #
    activity = models.PositiveSmallIntegerField(default=1, null=True) # for starting radio group
    cal_adj= models.IntegerField(default=1, null=True) # for starting radio group
    bmr = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    tdee = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    age_update_dt = models.DateField(null=True)
    multi_planner_flg = models.BooleanField(default=False) # Plan for other people.
    planner = models.ForeignKey('self', null=True, related_name='plannee', on_delete=models.SET_NULL)
    first_session = models.BooleanField(default=True)
    cal = models.BooleanField(default=True)
    pro =models.BooleanField(default=True)
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
# Requirements - can have defaults since have the boolean fields
    cal_req = models.DecimalField(max_digits=7, decimal_places=2, default=2000)
    pro_perc = models.DecimalField(max_digits=3, decimal_places=2, default=0.25, blank=True)  # Default needs to change
    car_perc = models.DecimalField(max_digits=3, decimal_places=2, default=0.4, blank=True)
    fat_perc = models.DecimalField(max_digits=3, decimal_places=2, default=0.35, blank=True)
    stf_thr = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    fib_req = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    sug_thr = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    sod_thr = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    cho_thr = models.DecimalField(max_digits=6, decimal_places=2,null=True, blank=True) # must opt-in for dietary cholesterol reqs. But default is 300 / Decimal(2000)
    clc_req = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    irn_req = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    vta_req = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    vtc_req = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    nsu_req = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    nca_req = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    # Upper and lower Bounds
    cal_ub = models.DecimalField(max_digits=6, decimal_places=2, default=2100, blank=True)
    cal_lb = models.DecimalField(max_digits=6, decimal_places=2, default=1900, blank=True)
    pro_ub = models.DecimalField(max_digits=6, decimal_places=2, default=131, blank=True) # Whole amount
    pro_lb = models.DecimalField(max_digits=6, decimal_places=2, default=119, blank=True) 
    car_ub = models.DecimalField(max_digits=6, decimal_places=2, default=210, blank=True)
    car_lb = models.DecimalField(max_digits=6, decimal_places=2, default=190, blank=True)
    fat_ub = models.DecimalField(max_digits=6, decimal_places=2, default=82, blank=True) 
    fat_lb = models.DecimalField(max_digits=6, decimal_places=2, default=74, blank=True) 
    stf_ub = models.DecimalField(max_digits=6, decimal_places=2, default=20, blank=True)
    stf_lb = models.DecimalField(max_digits=6, decimal_places=2, default=0, blank=True)
    fib_ub = models.DecimalField(max_digits=6, decimal_places=2, default=45, blank=True) # 45g 
    fib_lb = models.DecimalField(max_digits=6, decimal_places=2, default=25, blank=True) 
    sug_ub = models.DecimalField(max_digits=6, decimal_places=2, default=50, blank=True) 
    sug_lb = models.DecimalField(max_digits=6, decimal_places=2, default=0, blank=True) # 0g
    sod_ub = models.DecimalField(max_digits=6, decimal_places=2, default=2400, blank=True) 
    sod_lb = models.DecimalField(max_digits=6, decimal_places=2, default=500, blank=True) # 500mg
    cho_ub = models.DecimalField(max_digits=6, decimal_places=2, default=1000, blank=True)
    cho_lb = models.DecimalField(max_digits=6, decimal_places=2, default=0, blank=True)
    clc_ub = models.DecimalField(max_digits=7, decimal_places=2, default=2000, blank=True)
    clc_lb = models.DecimalField(max_digits=7, decimal_places=2, default=1000, blank=True)
    irn_ub = models.DecimalField(max_digits=6, decimal_places=2, default=45, blank=True)
    irn_lb = models.DecimalField(max_digits=6, decimal_places=2, default=18, blank=True)
    vta_ub = models.DecimalField(max_digits=7, decimal_places=2, default=10000, blank=True)
    vta_lb = models.DecimalField(max_digits=7, decimal_places=2, default=5000, blank=True)
    vtc_ub = models.DecimalField(max_digits=6, decimal_places=2, default=2000, blank=True)
    vtc_lb = models.DecimalField(max_digits=6, decimal_places=2, default=90, blank=True)
    nsu_ub = models.DecimalField(max_digits=6, decimal_places=2, default=45, blank=True)
    nsu_lb = models.DecimalField(max_digits=6, decimal_places=2, default=0, blank=True)
    nca_ub = models.DecimalField(max_digits=6, decimal_places=2, default=165, blank=True)
    nca_lb = models.DecimalField(max_digits=6, decimal_places=2, default=145, blank=True)

    @property
    def carb_g_req(self):
        return round((self.carb_perc*self.cal_req)/4,2)

    @property
    def fat_g_req(self):
        return round((self.fat_perc*self.cal_req)/9,2)

    @property
    def prot_g_req(self):
        return round((self.prot_perc*self.cal_req)/4,2)

    # Need to add essential fatty acids
    def __str__(self):
        return self.user

class PersonalProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    website = models.URLField(null=True)
    bio = models.TextField(null=True)
    avatar = models.URLField(null=True)
    preferred_name= models.CharField(max_length=300)
    goals = models.CharField(null=True,max_length=500)
    max_menus = models.IntegerField(default=5)
    current_weight_lbs = models.FloatField(null=True)
    goal_weight_lbs = models.FloatField(null=True)
    plan_made_streak = models.IntegerField(default=0)
    calories_reached_streak = models.IntegerField(default=0)
    macros_reached_streak = models.IntegerField(default=0)
    default_nuts_reached_streak = models.IntegerField(default=0)

@receiver(pre_save, sender=User)
def update_username_from_email(sender, instance, **kwargs):
    """
    Before saving user
    """
    # is default when signing up manually but this is for social saves
    instance.username = instance.email

@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    """
    After saving user
    """
    if created: 
        Profile.objects.create(user=instance)
        # Create User Default Menus
        user_menu = UserMenu.objects.create(user=instance)
        new_br = PrefMenu.objects.create(user=instance,create_user=instance,default_flg=True, meal_type='Breakfast', menu_name="Default Breakfast")
        new_lu = PrefMenu.objects.create(user=instance,create_user=instance,default_flg=True, meal_type='Lunch',menu_name="Default Lunch")
        new_di = PrefMenu.objects.create(user=instance,create_user=instance,default_flg=True, meal_type='Dinner',menu_name="Default Dinner")
        new_sn = PrefMenu.objects.create(user=instance,create_user=instance,default_flg=True, meal_type='Snack',menu_name="Default Snack")
        user_menu.breakfast_prefmenu_id = new_br.id
        user_menu.lunch_prefmenu_id = new_lu.id
        user_menu. dinner_prefmenu_id = new_di.id
        user_menu.snack_prefmenu_id = new_sn.id
        user_menu.save()
        meal_type_menu_dict = {'Breakfast': new_br.id, 'Lunch':new_lu.id, 'Dinner':new_di.id, 'Snack':new_sn.id}
        # Assign all to User Default Menus
        fd_prefs = FoodPreferences.objects.filter(prefmenu_id__in=[85,86,87,88]) # Default Breakfast
        for fd in fd_prefs:
            FoodPreferences.objects.create(meal_type=fd.meal_type, prefmenu_id=meal_type_menu_dict[fd.meal_type],dish_num=fd.dish_num,food_id=fd.food_id )
        ml_prefs = MealPreferences.objects.filter(prefmenu_id__in=[85,86,87,88])
        for ml in ml_prefs:
            MealPreferences.objects.create(meal_type=ml.meal_type, prefmenu_id=meal_type_menu_dict[ml.meal_type],dish_num=ml.dish_num,meal_id=ml.meal_id)
        rest_prefs = RestaurantPreferences.objects.filter(prefmenu_id__in=[85,86,87,88])
        for rest in rest_prefs:
            RestaurantPreferences.objects.create(meal_type=rest.meal_type, prefmenu_id=meal_type_menu_dict[rest.meal_type],dish_num=rest.dish_num,restaurant_id=rest.restaurant_id)
        fd_tg_prefs = FoodTagPreferences.objects.filter(prefmenu_id__in=[85,86,87,88])
        for fd_tg in fd_tg_prefs:
            FoodTagPreferences.objects.create(meal_type=fd_tg.meal_type, prefmenu_id=meal_type_menu_dict[fd_tg.meal_type],dish_num=fd_tg.dish_num,tag_id=fd_tg.tag_id)
        ml_tg_prefs = MealTagPreferences.objects.filter(prefmenu_id__in=[85,86,87,88])
        for ml_tg in ml_tg_prefs:
            MealTagPreferences.objects.create(meal_type=ml_tg.meal_type, prefmenu_id=meal_type_menu_dict[ml_tg.meal_type],dish_num=ml_tg.dish_num,tag_id=ml_tg.tag_id)

        # profile
        personal_prof = PersonalProfile.objects.create(user=instance)
        auth = User.objects.get(id=instance.id)
        new_pref_name = ''
        if auth.first_name:
            new_pref_name += auth.first_name+" "
        if auth.last_name:
            new_pref_name += auth.last_name
        if len(new_pref_name)>0:
            personal_prof.preferred_name = new_pref_name
            personal_prof.save()

        # account
        user_acct = UserAccount.objects.create(user=instance)
        user_acct.trial_start_date = datetime.date.today()
        user_acct.save()

        # TODO - send welcome email
    instance.profile.save()

class FoodDishes(models.Model):
    user = models.ForeignKey(User, on_delete='CASCADE')
    food = models.ForeignKey(Foods, on_delete=models.CASCADE)
    dish = models.CharField(choices=dishes, default='Main Courses', max_length=20)
    standalone = models.BooleanField(default=False)

class MenuTags(models.Model):
    name = models.CharField(max_length=300, unique=True)

class PublicMenu(models.Model):
    create_user = models.ForeignKey(User, on_delete='CASCADE', default=5, related_name="public_menu_create_user")
    menu_name =  models.CharField(max_length=300)
    menu_description = models.TextField(null=True)
    image_url = models.URLField(default='https://planyourmealsmedia.s3.amazonaws.com/menu/default_thumbnail.png')
    tags = models.ManyToManyField(MenuTags, through="TaggedMenus")
    total_clones = models.IntegerField(default=0) # NOTE - this is not the current total clones
    current_clones = models.IntegerField(default=0) # This would be updated for old cloned_from and new_cloned_from at clone moment - probably not a good idea to have single source of truth
    breakfast_prefmenu = models.ForeignKey('PrefMenu', on_delete='CASCADE', related_name='public_br_prefmenu')
    lunch_prefmenu = models.ForeignKey('PrefMenu', on_delete='CASCADE', related_name='public_lu_prefmenu')
    dinner_prefmenu = models.ForeignKey('PrefMenu', on_delete='CASCADE', related_name='public_di_prefmenu')
    snack_prefmenu = models.ForeignKey('PrefMenu', on_delete='CASCADE', related_name='public_sn_prefmenu')

class TaggedMenus(models.Model):
    foodtag = models.ForeignKey(MenuTags, on_delete=models.CASCADE)
    menu = models.ForeignKey(PublicMenu, on_delete=models.CASCADE)
    added_by= models.ForeignKey(User, on_delete=models.SET_NULL, null=True) # should always be menu creator probably

class UserMenu(models.Model):
    user = models.ForeignKey(User, on_delete='CASCADE', related_name='user_menu_user')
    cloned_from = models.ForeignKey(PublicMenu, on_delete='SET_NULL', null=True)
    clone_date = models.DateField(null=True)
    breakfast_prefmenu = models.ForeignKey('PrefMenu', on_delete='CASCADE', related_name='user_br_prefmenu', null=True)
    lunch_prefmenu = models.ForeignKey('PrefMenu', on_delete='CASCADE', related_name='user_lu_prefmenu',null=True)
    dinner_prefmenu = models.ForeignKey('PrefMenu', on_delete='CASCADE', related_name='user_di_prefmenu',null=True)
    snack_prefmenu = models.ForeignKey('PrefMenu', on_delete='CASCADE', related_name='user_sn_prefmenu',null=True)

class PrefMenu(models.Model):
    """
    User Menu At Meal Level
    """
    create_user = models.ForeignKey(User, on_delete='CASCADE', default=5, related_name="created_user") # should delete
    user = models.ForeignKey(User, on_delete='CASCADE') # should delete (?)
    default_flg = models.BooleanField(default=False) 
    """
    default_flg is used right now. But the single source of truth for default flg should be ("is in UserMenu").
    Likewise, all prefMenus belonging to a UserMenu should have default=True. 
    AND, all PublicMenus should have default=False. 
    """
    menu_name = models.CharField(null=True, max_length=300) # should delete
    reusable_flg = models.BooleanField(default=False) # should delete
    public_flg = models.BooleanField(default=False) # should delete
    meal_type = models.CharField(choices=meals, max_length=10, default="Any")
    # default repeat days

class FoodPreferences(models.Model):
    meal_type = models.CharField(choices=meals, max_length=10)
    prefmenu = models.ForeignKey(PrefMenu,on_delete='CASCADE', null=True)
    dish_num = models.CharField(choices=dishes, default='Whole Meal', max_length=20)
    food = models.ForeignKey(Foods, on_delete=models.CASCADE, null=True) # list of food_keys
    # max_servings = models.FloatField(default=4) # Putting in here as well as in food_foods so people can customize to their plans. 
    # max_num_per_week = models.FloatField(default=2) # This is used for foods, the one in prob_r is for other items in ___prefernces
    # rating

class MealPreferences(models.Model):
    meal_type = models.CharField(choices=meals, max_length=10)
    prefmenu = models.ForeignKey(PrefMenu,on_delete='CASCADE', null=True)
    dish_num = models.CharField(choices=dishes, default='Whole Meal', max_length=20)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, null=True) # list of food_keys

class RestaurantPreferences(models.Model):
    meal_type = models.CharField(choices=meals, max_length=10)
    prefmenu = models.ForeignKey(PrefMenu,on_delete='CASCADE', null=True)
    dish_num = models.CharField(choices=dishes, default='Whole Meal', max_length=20)
    restaurant = models.ForeignKey(Restaurants, on_delete=models.CASCADE, null=True)

class FoodTagPreferences(models.Model):
    meal_type = models.CharField(choices=meals, max_length=10)
    prefmenu = models.ForeignKey(PrefMenu,on_delete='CASCADE', null=True)
    dish_num = models.CharField(choices=dishes, default='Whole Meal', max_length=20)  
    tag =  models.ForeignKey(FoodTags, on_delete=models.CASCADE, null=True)

class MealTagPreferences(models.Model):
    meal_type = models.CharField(choices=meals, max_length=10)
    prefmenu = models.ForeignKey(PrefMenu,on_delete='CASCADE', null=True)
    dish_num = models.CharField(choices=dishes, default='Whole Meal', max_length=20) 
    tag =  models.ForeignKey(MealTags, on_delete=models.CASCADE, null=True)

class GlobalProbRejectFood(models.Model):
    """
    This whole table should be periodically update by scheduled batch process
    """
    food = models.ForeignKey(Foods, on_delete=models.CASCADE, related_name='global_pref_food')
    global_star_rating = models.FloatField(default=2.5)
    global_total_uses = models.IntegerField(default=0)
    # Should add n-uses for various reasons - actually that should be baked into the global prob_r calculation
    prob_r = models.DecimalField(max_digits=5, decimal_places=4, default=0.8500) # calculated by the average user score. Updated via batch. Used to seed probabilities for new users

class UserProbRejectFood(models.Model):
    """
    For calculating 
    """
    food = models.ForeignKey(Foods, on_delete=models.CASCADE, related_name='local_pref_food')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    viewed = models.IntegerField(default=0) # Number of times the food was added to plan by either MPG or user
    removed = models.IntegerField(default=0) # Number of times the food was removed by user
    user_total_uses = models.IntegerField(default=0)
    dislike_ind = models.IntegerField(default=0)
    last_view = models.DateField(default=datetime.date(2018,1,1))
    last_use = models.DateField(default=datetime.date(2018,1,1))
    user_star_rating = models.FloatField(default=2.5)
    max_servings = models.FloatField(default=4)
    max_num_per_week = models.FloatField(default=2)
    default_dish_num = models.CharField(choices=dishes, default='Whole Meal', max_length=20)
    # Also should add an 'in-pantry option'

    @property
    def prob_r(self):
        if self.viewed ==0:
            like_ratio = 0.5
            last_use = 0
            total_uses = 2
        else:
            like_ratio = self.removed/self.viewed
            total_uses = 1/min((self.uses-self.removed), 20) # max is 1, min is 1/20
            last_use = 1/((datetime.date.today()-self.last_use).days + 0.05) # 
        
        return like_ratio * 0.5 + last_use * 0.2 + total_uses * 0.3 + self.dislike_ind * 0.2
    # Will add noise in the query
    # This still needs a 'preference' score based on category / string, etc

class ViewedToday(models.Model):
    """
    For Storing if a single food was shown to a user at least once in a single day
    """
    food = models.ForeignKey(Foods, on_delete=models.CASCADE, related_name='viewed_today_food')

class GlobalProbRejectMeal(models.Model):
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='global_pref_meal')
    prob_r = models.DecimalField(max_digits=5, decimal_places=4, default=0.8500) # calculated by the average user score. Updated via batch. Used to seed probabilities for new users

class UserProbRejectMeal(models.Model):
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='local_pref_meal')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    viewed = models.IntegerField(default=0) # Number of times the food was added to plan by either MPG or user
    removed = models.IntegerField(default=0) # Number of times the food was removed by user
    user_total_uses = models.IntegerField(default=0)
    dislike_ind = models.IntegerField(default=0)
    last_view = models.DateField(default=datetime.date(2018,1,1))
    last_use = models.DateField(default=datetime.date(2018,1,1))
    user_star_rating = models.FloatField(default=2.5)
    max_servings = models.FloatField(default=2)
    # may want to add the ability to pause a meal for a few days (pause and select n days)

    @property
    def prob_r(self):
        if self.viewed ==0:
            like_ratio = 0.5
            last_use = 0
            total_uses = 2
        else:
            like_ratio = self.removed/self.viewed
            total_uses = 1/min((self.uses-self.removed), 20) # max is 1, min is 1/20
            last_use = 1/((datetime.date.today()-self.last_use).days + 0.5) # 
        
        return like_ratio * 0.5 + last_use * 0.2 + total_uses * 0.3 + self.dislike_ind * 0.2 

# NEED A BATCH SCRIPT TO REMOVE OLD EXCLUSIONS
class ExcludeFoods(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    food=models.ForeignKey(Foods, on_delete=models.CASCADE)
    start_dt = models.DateField(default=datetime.datetime.now)
    end_dt = models.DateField(default=datetime.datetime.now)

class ExcludeMeals(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
    start_dt = models.DateField(default=datetime.datetime.now)
    end_dt = models.DateField(default=datetime.datetime.now)

class NutrientInfo(models.Model):
    nutrient = models.CharField(max_length=50)
    info = models.TextField()
    info_source = models.URLField()

class ProbRejectCoefficients(models.Model):
    """
    Coefficients that apply to both food and meals for 'probability to reject'
    """
    item_type = models.CharField(max_length=4) # food or meal
    keep_ratio = models.FloatField(default=0) # ratio of times kept vs removed (total uses / total views)
    days_since_view = models.FloatField(default=0) # days since last view
    days_since_use = models.FloatField(default=0) # days since last use
    random_var = models.FloatField(default=0) # random factor
    inv_stars_mult = models.FloatField(default=0) # user-given stars
    inv_total_uses = models.FloatField(default=0) # inverse of total uses

class UserAccount(models.Model):
    """
    User membership information
    """
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    signup_dt = models.DateField(default=datetime.datetime.now)
    status = models.CharField(default='trial', max_length=30) # full, free
    stripe_cust_id = models.CharField(max_length=300, null = True)
    stripe_sub_id = models.CharField(max_length=300, null = True)
    trial_start_date = models.DateField(null=True)
    trial_completed = models.BooleanField(default=False) # needs to be updated in daily batch
    status_start_date = models.DateField(null=True) # only set when starting subscription. Set to null on cancel
    status_end_date = models.DateField(null=True) # only set if user is one 
    always_full = models.BooleanField(default=False) # users who always get access without paying 
    # Email opt-in / opt-out settings
    transactional_emails = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=True)
    notification_emails = models.BooleanField(default=True)
    # To delete - user has requested delete account
    requested_delete = models.BooleanField(default=False)
    delete_request_dt = models.DateField(null=True)
    # Core user account date 

# menu maker acct

msg_choices=(('delete','delete'),
            ('bug','bug'),
            ('feature', 'feature'),
            ('data', 'data'),
            ('help','help'),
            ('other', 'other')
            )
class UserMessage(models.Model):
    """
    Planner messages. Can include
        * deleting user data (compliance)
        * bug reporting
        * feature requests
        * food requests
        * other
    """
    user= models.ForeignKey(User,on_delete=models.CASCADE)
    message_dt = models.DateField(default=datetime.datetime.now)
    message_type = models.CharField(choices=msg_choices, max_length=30)
    message_text = models.TextField(null=True)
    resolved=models.BooleanField(default=False)

class Blog(models.Model):
    title = models.CharField(max_length=300)
    slug=models.SlugField(max_length=100, unique=True) # change to slugfield
    post = MarkdownxField()
    title_image=models.URLField() # change to imagefield
    published = models.DateField(default=timezone.now())
    embed_media = models.TextField(blank=True, null=True)
