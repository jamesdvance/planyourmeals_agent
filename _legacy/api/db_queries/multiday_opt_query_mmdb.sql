
;
/* All meals from menus (assume included default menus 
*Not including exclusions for simplicity*
*/
select * from plan_food_amount where serving_size_idx <> 0;
/* All Meals From Menus */
SELECT
  fa.meal_id as unique_id,
  cast('meal' as char(4)) as fd_type,
  m.meal_type as meal,
  m.dish_num as dish_num,
  'menu' as menu_type,
  m.prefmenu_id as menu_id,
  pr.viewed,
  pr.removed,
  pr.dislike_ind,
  pr.last_view,
  pr.max_servings,
  p.mealname as description,
  sum(f.calories*(fa.amount/fa.amount_divisor)) as calories,
  sum(f.protein_g *(fa.amount/fa.amount_divisor)) as protein_g,
  sum(f.fat_g *(fa.amount/fa.amount_divisor)) as fat_g,
  sum(f.carb_g*(fa.amount/fa.amount_divisor)) as carb_g,
  sum(f.saturated_fat_g*(fa.amount/fa.amount_divisor)) as saturated_fat_g,
  sum(f.fiber_g*(fa.amount/fa.amount_divisor)) as fiber_g, 
  sum(f.sugar_g*(fa.amount/fa.amount_divisor)) as sugar_g, 
  sum(f.sodium_mg*(fa.amount/fa.amount_divisor)) as sodium_mg, 
  sum(f.cholesterol_mg*(fa.amount/fa.amount_divisor)) as cholesterol_mg,
  sum(f.calcium_mg*(fa.amount/fa.amount_divisor)) as calcium_mg,
  sum(f.iron_mg*(fa.amount/fa.amount_divisor)) as iron_mg,
  sum(f.vit_a_mcg*(fa.amount/fa.amount_divisor)) as vit_a_mcg,
  sum(f.vit_c_mg*(fa.amount/fa.amount_divisor)) as vit_c_mg

  from plan_meal p

  join plan_food_amount fa 
    on p.id = fa.meal_id

  join food_foods f 
    on fa.food_id = f.food_key

  join core_mealpreferences m
    on p.id = m.meal_id
    and p.meal_type = m.meal_type

  left join core_UserProbRejectMeal pr 
    on p.id = pr.meal_id
    and pr.user_id = 2

  where m.meal_type in ('Breakfast', 'Lunch', 'Dinner', 'Snack') and m.prefmenu_id in (9,10,11,12)

  group by fa.meal_id, m.meal_type,m.dish_num,cast('menu' as char(4)), m.prefmenu_id, pr.viewed, pr.removed, pr.dislike_ind,pr.last_view,pr.max_servings,p.mealname

union 
/* All foods from menus */

select
f.food_key  as unique_id,
cast('food' as char(4)) as fd_type,
m.meal_type,
m.dish_num,
'menu' as menu_type,
m.prefmenu_id as menu_id,
pr.viewed,
pr.removed,
pr.dislike_ind,
pr.last_view,
pr.max_servings,
f.food_description as description,
f.calories,
f.protein_g,
f.fat_g,
f.carb_g,
f.saturated_fat_g,
f.fiber_g, 
f.sugar_g, 
f.sodium_mg, 
f.cholesterol_mg,
f.calcium_mg,
f.iron_mg,
f.vit_a_mcg,
f.vit_c_mg
from core_foodpreferences m

join food_foods f 
on m.food_id = f.food_key 

left join core_userprobrejectfood pr 
on f.food_key = pr.food_id
and pr.user_id = 2

where m.meal_type in ('Breakfast', 'Lunch', 'Dinner', 'Snack') and m.prefmenu_id in (9,10,11,12)


union
/* all foods from restaurants from menus*/
select
f.food_key  as unique_id,
cast('food' as char(4)) as fd_type,
m.meal_type,
m.dish_num,
'menu' as menu_type,
m.prefmenu_id as menu_id,
pr.viewed,
pr.removed,
pr.dislike_ind,
pr.last_view,
pr.max_servings,
f.food_description as description,
f.calories,
f.protein_g,
f.fat_g,
f.carb_g,
f.saturated_fat_g,
f.fiber_g, 
f.sugar_g, 
f.sodium_mg, 
f.cholesterol_mg,
f.calcium_mg,
f.iron_mg,
f.vit_a_mcg,
f.vit_c_mg

from core_restaurantpreferences m

join food_foods f 
on m.restaurant_id = f.restaurant_id

left join core_userprobrejectfood pr 
on pr.user_id = 2
and f.food_key = pr.food_id

where m.meal_type in ('Breakfast', 'Lunch', 'Dinner', 'Snack') and m.prefmenu_id in (5,6,7,8)

union
/* all foods from tags from menu */
select
f.food_key  as unique_id,
cast('food' as char(4)) as fd_type,
m.meal_type,
m.dish_num,
'menu' as menu_type,
m.prefmenu_id as menu_id,
pr.viewed,
pr.removed,
pr.dislike_ind,
pr.last_view,
pr.max_servings,
f.food_description as description,
f.calories,
f.protein_g,
f.fat_g,
f.carb_g,
f.saturated_fat_g,
f.fiber_g, 
f.sugar_g, 
f.sodium_mg, 
f.cholesterol_mg,
f.calcium_mg,
f.iron_mg,
f.vit_a_mcg,
f.vit_c_mg

from core_foodtagpreferences m

join food_taggedfoods t
  on m.tag_id = t.foodtag_id

join food_foods f 
  on t.foods_id = f.food_key

left join core_userprobrejectfood pr 
  on pr.user_id = 2
  and f.food_key = pr.food_id

where m.meal_type in ('Breakfast', 'Lunch', 'Dinner', 'Snack') and m.prefmenu_id in (9,10,11,12);
 
/* Meal Opt Restaurant Query (For a Starbucks Breakfast */
select
f.food_key  as unique_id,
cast('food' as char(4)) as fd_type,
'Breakfast' as meal,
'placeholder' as dish_num,
'restaurant' as menu_type,
f.restaurant_id as menu_id,
pr.viewed,
pr.removed,
pr.dislike_ind,
pr.last_view,
pr.max_servings,
f.calories,
f.protein_g,
f.fat_g,
f.carb_g,
f.saturated_fat_g,
f.fiber_g, 
f.sugar_g, 
f.sodium_mg, 
f.cholesterol_mg,
f.calcium_mg,
f.iron_mg,
f.vit_a_mcg,
f.vit_c_mg

from  food_foods f 

left join core_userprobrejectfood pr 
on f.food_key = pr.food_id

where pr.user_id=2 and f.restaurant_id in (368);

select
*
from core_userprobrejectfood ;

select * from food_foods limit 20;

/* Full combo query */

		SELECT
			  fa.meal_id as unique_id,
			  cast('meal' as char(4)) as fd_type,
			  m.meal_type as meal,
			  m.dish_num as dish_num,
			  'menu' as menu_type,
			  m.prefmenu_id as menu_id,
			  pr.viewed,
			  pr.removed,
			  pr.dislike_ind,
			  pr.last_view,
			  pr.max_servings,
			  sum(f.calories*(fa.amt/fa.amount_divisor)) as calories,
			  sum(f.protein_g *(fa.amt/fa.amount_divisor)) as protein_g,
			  sum(f.fat_g *(fa.amt/fa.amount_divisor)) as fat_g,
			  sum(f.carb_g*(fa.amt/fa.amount_divisor)) as carb_g,
			  sum(f.saturated_fat_g*(fa.amt/fa.amount_divisor)) as saturated_fat_g,
			  sum(f.fiber_g*(fa.amt/fa.amount_divisor)) as fiber_g, 
			  sum(f.sugar_g*(fa.amt/fa.amount_divisor)) as sugar_g, 
			  sum(f.sodium_mg*(fa.amt/fa.amount_divisor)) as sodium_mg, 
			  sum(f.cholesterol_mg*(fa.amt/fa.amount_divisor)) as cholesterol_mg,
			  sum(f.calcium_mg*(fa.amt/fa.amount_divisor)) as calcium_mg,
			  sum(f.iron_mg*(fa.amt/fa.amount_divisor)) as iron_mg,
			  sum(f.vit_a_mcg*(fa.amt/fa.amount_divisor)) as vit_a_mcg,
			  sum(f.vit_c_mg*(fa.amt/fa.amount_divisor)) as vit_c_mg
		FROM plan_meal p

		JOIN plan_food_amount fa 
			ON p.id = fa.meal_id

		JOIN food_foods f 
		    ON fa.food_id = f.food_key

		JOIN core_mealpreferences m
			ON p.id = m.meal_id
			AND p.meal_type = m.meal_type

  		LEFT JOIN core_UserProbRejectMeal pr 
		    ON p.id = pr.meal_id
		    AND pr.user_id = 2

		WHERE  m.prefmenu_id IN (9,10,11,12)
			AND not exists
			  (
			    SELECT
			    1
			    FROM core_excludefoods excl
			    WHERE excl.food_id = f.food_key
			      AND excl.user_id = pr.user_id
			      AND excl.start_dt <= '2019-11-17' and excl.end_dt >= '2019-11-23'
			  )
		GROUP BY fa.meal_id, m.meal_type,m.dish_num,cast('menu' as char(4)), m.prefmenu_id, pr.viewed, pr.removed, pr.dislike_ind,pr.last_view,pr.max_servings

		UNION
		/* All foods from menus */
		SELECT
			f.food_key  as unique_id,
			cast('food' as char(4)) as fd_type,
			m.meal_type as meal,
			m.dish_num,
			'menu' as menu_type,
			m.prefmenu_id as menu_id,
			pr.viewed,
			pr.removed,
			pr.dislike_ind,
			pr.last_view,
			pr.max_servings,
			f.calories,
			f.protein_g,
			f.fat_g,
			f.carb_g,
			f.saturated_fat_g,
			f.fiber_g, 
			f.sugar_g, 
			f.sodium_mg, 
			f.cholesterol_mg,
			f.calcium_mg,
			f.iron_mg,
			f.vit_a_mcg,
			f.vit_c_mg
		FROM core_foodpreferences m

		JOIN food_foods f 
			ON m.food_id = f.food_key 

		LEFT JOIN core_userprobrejectfood pr 
			ON f.food_key = pr.food_id
			AND pr.user_id = 2

		WHERE  m.prefmenu_id IN (9,10,11,12)
			AND not exists
			  (
			    SELECT
			    1
			    FROM core_excludefoods excl
			    WHERE excl.food_id = f.food_key
			      AND excl.user_id = pr.user_id
			      AND excl.start_dt <= '2019-11-17' and excl.end_dt >= '2019-11-23'
			  )
		UNION
		/* all foods from restaurants from menus*/
		SELECT
			f.food_key  as unique_id,
			cast('food' as char(4)) as fd_type,
			m.meal_type as meal,
			m.dish_num,
			'menu' as menu_type,
			m.prefmenu_id as menu_id,
			pr.viewed,
			pr.removed,
			pr.dislike_ind,
			pr.last_view,
			pr.max_servings,
			f.calories,
			f.protein_g,
			f.fat_g,
			f.carb_g,
			f.saturated_fat_g,
			f.fiber_g, 
			f.sugar_g, 
			f.sodium_mg, 
			f.cholesterol_mg,
			f.calcium_mg,
			f.iron_mg,
			f.vit_a_mcg,
			f.vit_c_mg

		FROM core_restaurantpreferences m

		JOIN food_foods f 
			ON m.restaurant_id = f.restaurant_id

		LEFT JOIN core_userprobrejectfood pr 
			ON pr.user_id = 2
			AND f.food_key = pr.food_id

		WHERE m.prefmenu_id IN (5,6,7,8)
			AND not exists
			  (
			    SELECT
			    1
			    FROM core_excludefoods excl
			    WHERE excl.food_id = f.food_key
			      AND excl.user_id = pr.user_id
			      AND excl.start_dt <= '2019-11-17' and excl.end_dt >= '2019-11-23'
			  )
		UNION
			/* all foods from tags from menu */
		SELECT
			f.food_key  as unique_id,
			cast('food' as char(4)) as fd_type,
			m.meal_type as meal,
			m.dish_num,
			'menu' as menu_type,
			m.prefmenu_id as menu_id,
			pr.viewed,
			pr.removed,
			pr.dislike_ind,
			pr.last_view,
			pr.max_servings,
			f.calories,
			f.protein_g,
			f.fat_g,
			f.carb_g,
			f.saturated_fat_g,
			f.fiber_g, 
			f.sugar_g, 
			f.sodium_mg, 
			f.cholesterol_mg,
			f.calcium_mg,
			f.iron_mg,
			f.vit_a_mcg,
			f.vit_c_mg

		FROM core_foodtagpreferences m

		JOIN food_taggedfoods t
			ON m.tag_id = t.foodtag_id

		JOIN food_foods f 
			ON t.foods_id = f.food_key

		LEFT JOIN core_userprobrejectfood pr 
			ON pr.user_id = 2
			AND f.food_key = pr.food_id

		WHERE m.prefmenu_id IN (5,6,7,8)
			AND not exists
			  (
			    SELECT
			    1
			    FROM core_excludefoods excl
			    WHERE excl.food_id = f.food_key
			      AND excl.user_id = pr.user_id
			      AND excl.start_dt <= '2019-11-17' and excl.end_dt >= '2019-11-23'
			  )
		UNION 
		/* Standalone food tag query */
		SELECT
			f.food_key  as unique_id,
			cast('food' as char(4)) as fd_type,
			'placeholder' as meal,
			f.default_dish_num as dish_num,
			'tag' as menu_type, 
			t.id as menu_id,
			pr.viewed,
			pr.removed,
			pr.dislike_ind,
			pr.last_view,
			pr.max_servings,
			f.calories,
			f.protein_g,
			f.fat_g,
			f.carb_g,
			f.saturated_fat_g,
			f.fiber_g, 
			f.sugar_g, 
			f.sodium_mg, 
			f.cholesterol_mg,
			f.calcium_mg,
			f.iron_mg,
			f.vit_a_mcg,
			f.vit_c_mg

		FROM food_taggedfoods t

		JOIN food_foods f 
			ON t.foods_id = f.food_key

		LEFT JOIN core_userprobrejectfood pr 
			ON f.food_key = pr.food_id

		WHERE pr.user_id = 2  AND t.foodtag_id IN (2,3,4)
			AND NOT EXISTS
			(
				SELECT
				1
				FROM core_excludefoods excl
				WHERE excl.food_id = pr.food_id
				AND excl.user_id = pr.user_id
				AND excl.start_dt <= '2019-11-17' and excl.end_dt >= '2019-11-23'
			)
		UNION 
		/* Queries standalone restaurant options */
		SELECT
			f.food_key  as unique_id,
			cast('food' as char(4)) as fd_type,
			'placeholder' as meal,
			f.default_dish_num as dish_num,
			'restaurant' as menu_type, 
			f.restaurant_id as menu_id,
			pr.viewed,
			pr.removed,
			pr.dislike_ind,
			pr.last_view,
			pr.max_servings,
			f.calories,
			f.protein_g,
			f.fat_g,
			f.carb_g,
			f.saturated_fat_g,
			f.fiber_g, 
			f.sugar_g, 
			f.sodium_mg, 
			f.cholesterol_mg,
			f.calcium_mg,
			f.iron_mg,
			f.vit_a_mcg,
			f.vit_c_mg

		FROM  food_foods f 

		LEFT JOIN core_userprobrejectfood pr 
		ON f.food_key = pr.food_id

		WHERE  pr.user_id=2 AND f.restaurant_id IN (368)
		AND NOT EXISTS
		  (
		    SELECT
		    1
		    FROM core_excludefoods excl
		    WHERE excl.food_id = f.food_key
		      AND excl.user_id = pr.user_id
		      AND excl.start_dt <= '2019-11-17' and excl.end_dt >= '2019-11-23'
		  );

select
*
from plan_meal;

select
*
from plan_food_amount;
