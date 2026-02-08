select 
*
from plan_planmeal
limit 10;

select 
*
from plan_meal
limit 10;

select 
*
from plan_food_amount
limit 10;

select
  p.plan_date,
  p.meal_type,
  am.meal_id,
  am.amt,
  am.serving_size_idx,
  f.food_key,
  f.food_description,
  f.brand,
  f.food_type_grp,
  f.calories, 
  f.protein_g,
  f.fat_g,
  f.carb_g,
  f.fiber_g,
  f.calcium_mg,
  f.iron_mg,
  f.vit_a_mcg,
  f.vit_c_mg,
  f.image_url,
  ss.serving_sizes

from plan_planmeal p
join plan_meal m
   on p.meal_id=m.id
join plan_food_amount am
  on m.id = am.meal_id
join food_foods f
  on f.food_key = am.food_id
join food_altservingsize ss
  on f.food_key = ss.food_id
where plan_date = '2019-10-24' and p.meal_type='Breakfast';

select
*
from plan_planmeal p
join plan_meal m
  on p.meal_id = m.id
join plan_food_amount am
  on am.meal_id = m.id
join food_foods f
  on am.food_id = f.food_key
where plan_date = '2019-10-27';

delete from plan_food_amount where food_id = 473080;
commit;

select * from food_altservingsize where 
