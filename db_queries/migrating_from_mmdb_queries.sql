
/* Going in order that models appear in django script */

/* Foods */
--all
select *from food_foodtags;
select *from food_foodtags;
select *from food_taggedfoods;
select *from food_restaurants;
select * from food_foods;
select * from food_rawingredients;
select * from food_foodindex;
select * from food_altservingsize;
select * from food_recipesource;
select * from food_recipes;
select * from food_recipefood;

/* Plan */
-- just saved meals and food amounts
select * from core_prefmenu;
/* Core */
-- just prefmenu
-- will need to adjust ids on the default prefmenu
