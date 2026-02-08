
;
/* All meals from menus (assume included default menus 
*Not including exclusions for simplicity*
*/
select * from plan_food_amount where serving_size_idx <> 0;

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
			  cast(1 as int) as max_num_per_week,
			  cast(1 as int) as serving_size_val,
			  
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

		WHERE  m.prefmenu_id IN (5,6,7,8)

		GROUP BY fa.meal_id, m.meal_type,m.dish_num,cast('menu' as char(4)), m.prefmenu_id, 
			pr.viewed, pr.removed, pr.dislike_ind,pr.last_view,pr.max_servings, cast(1 as int),cast(1 as int)
  
;
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

  where m.meal_type in ('Breakfast', 'Lunch', 'Dinner', 'Snack') and m.prefmenu_id in (5,6,7,8)

  group by fa.meal_id, m.meal_type,m.dish_num,cast('menu' as char(4)), m.prefmenu_id, pr.viewed, pr.removed, pr.dislike_ind,pr.last_view,pr.max_servings
