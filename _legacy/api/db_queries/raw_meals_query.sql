		SELECT
		  m.id as meal_id,
		  m.mealname,
		  m.cloned_n,
		  concat(f.food_key,'_','searchResults','_meal_',m.id) as drag_id,
		  am.amt,
		  am.serving_size_idx,
      f.food_key,
		  f.food_description,
		  f.brand,
		  f.serving_size_val,
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

		FROM plan_meal m
		JOIN plan_food_amount am
		  ON m.id = am.meal_id
		JOIN food_foods f
		  ON f.food_key = am.food_id
		JOIN food_altservingsize ss
		  ON f.food_key = ss.food_id
		WHERE m.mealname like '%chicken%' ;
