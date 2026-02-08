
select
food_key,
food_description,
brand,	
food_type_grp,
serving_size_unit,
serving_size_val
from food_foods
;

select * from food_foods where food_type_grp = 'recipe' limit 200;
select * from food_recipes;
select * from food_recipefood where ingred_food_id is null;

select food_description, ingred
