import pandas as pd

def query_datasets(connection,user_id,menus_list, week_start_dt, week_end_dt):
	"""
		Cycles through database and queries tag, restaurant and menu datasets
	"""
	tag_id_list = [0]
	rest_id_list = [0]
	menu_id_list = [0]
	meal_type_list = []
	meals_idx_tup = []
	days_list = []
	has_menu = False
	has_tag = False
	has_rest = False

	for menu_dict in menus_list:
		"""
		Loop through menus_dict and creates data structures necessary for building the optimization inputs. 
		Includes:
			* tag_id_list, rest_id_list, menu_id_list - unique lists of ids for each query
			* meals_idx_tup - list of tuples for each combination of day, meal
			* days_list - unique list of each day in the dataset
			* has_menu, has_tag, has_rest flags - flags to determine if queries to each db is necessary
		"""
		for meal in menu_dict['meals']:
			days_list.append(menu_dict['day'])
			meals_idx_tup.append((menu_dict['day'], meal['meal']))
			for menu in meal['menus']:
				if menu['type'] == 'menu':
					has_menu = True
					menu_id_list.append(menu['id'])
					if meal['meal'] not in meal_type_list:
						meal_type_list.append(meal['meal'])
				elif menu['type'] == 'tag':
					has_tag = True
					food_tag_list = food_tag_list.append(menu['id'])
				elif menu['type'] == 'restaurant':
					has_rest = True
					rest_id_list.append(menu['id'])
				else:
					pass
		# Make Id Lists Unique
	tag_id_tup = tuple(set(tag_id_list))
	rest_id_tup = tuple(set(rest_id_list))
	menu_id_tup = tuple(set(menu_id_list))
	qry = all_menu_opts_qry_odbc(user_id, menu_id_list, week_start_dt, week_end_dt, tag_id_list, rest_id_list)
	# Build return df with queries
	return_df = pd.read_sql(sql=qry, con=connection, parse_dates=['last_view'])
	return return_df, meals_idx_tup, list(set(days_list))

def all_menu_opts_qry_odbc(user_id, menu_id_list, week_start_dt, week_end_dt, tag_id_list, rest_id_list):
	"""
		Query that combines the menu queries for each tag, rest, and menu id list
		Query parameters:
			* user_id - id of the user. Used for building blocks of 'prob_r' target variable
			* menu_id_tup - id of every menu to be queried (TUPLE)
			* week_start_dt - earliest date to include in exclusion check
			* week_end_dt - latest date to include in exclusion check
			* tag_id_tup - id of every tag to be queried via standalone select (TUPLE)
			* rest_id_tup - id of every restaurant to be queried via standalone select (TUPLE)
	"""
	menu_id_list_str = '('
	for id in menu_id_list:
		menu_id_list_str += str(id)+","
	menu_id_list_str = menu_id_list_str[0:len(menu_id_list_str)-1]
	menu_id_list_str += ')'
	print(menu_id_list_str)
	
	tag_id_list_str = '('
	for id in tag_id_list:
		tag_id_list_str += str(id)+","
	tag_id_list_str = tag_id_list_str[0:len(tag_id_list_str)-1]
	tag_id_list_str += ')'
	print(tag_id_list_str)
	
	rest_id_list_str = '('
	for id in rest_id_list:
		rest_id_list_str += str(id)+","
	rest_id_list_str = rest_id_list_str[0:len(rest_id_list_str)-1]
	rest_id_list_str += ')'
	print(rest_id_list_str)

	return """		
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
			  f.serving_size_val,
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
		    AND pr.user_id = {user_id}

		WHERE  m.prefmenu_id IN {menu_id_list}
			AND not exists
			  (
			    SELECT
			    1
			    FROM core_excludefoods excl
			    WHERE excl.food_id = f.food_key
			      AND excl.user_id = pr.user_id
			      AND excl.start_dt <= {week_start_dt} and excl.end_dt >= {week_end_dt}
			  )
		GROUP BY fa.meal_id, m.meal_type,m.dish_num,cast('menu' as char(4)), m.prefmenu_id, pr.viewed, pr.removed, pr.dislike_ind,pr.last_view,pr.max_servings,f.serving_size_val

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
			f.serving_size_val,
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
			AND pr.user_id = {user_id}

		WHERE  m.prefmenu_id IN {menu_id_list}
			AND not exists
			  (
			    SELECT
			    1
			    FROM core_excludefoods excl
			    WHERE excl.food_id = f.food_key
			      AND excl.user_id = pr.user_id
			      AND excl.start_dt <= {week_start_dt} and excl.end_dt >= {week_end_dt}
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
			f.serving_size_val,
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
			ON pr.user_id = {user_id}
			AND f.food_key = pr.food_id

		WHERE m.prefmenu_id IN {menu_id_list}
			AND not exists
			  (
			    SELECT
			    1
			    FROM core_excludefoods excl
			    WHERE excl.food_id = f.food_key
			      AND excl.user_id = pr.user_id
			      AND excl.start_dt <= {week_start_dt} and excl.end_dt >= {week_end_dt}
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
			f.serving_size_val,
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
			ON pr.user_id = {user_id}
			AND f.food_key = pr.food_id

		WHERE m.prefmenu_id IN {menu_id_list}
			AND not exists
			  (
			    SELECT
			    1
			    FROM core_excludefoods excl
			    WHERE excl.food_id = f.food_key
			      AND excl.user_id = pr.user_id
			      AND excl.start_dt <= {week_start_dt} and excl.end_dt >= {week_end_dt}
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
			f.serving_size_val,
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

		WHERE pr.user_id = {user_id}  AND t.foodtag_id IN {tag_id_list}
			AND NOT EXISTS
			(
				SELECT
				1
				FROM core_excludefoods excl
				WHERE excl.food_id = pr.food_id
				AND excl.user_id = pr.user_id
				AND excl.start_dt <= {week_start_dt} and excl.end_dt >= {week_end_dt}
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
			f.serving_size_val,
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

		WHERE  pr.user_id={user_id} AND f.restaurant_id IN {rest_id_list}
		AND NOT EXISTS
		  (
		    SELECT
		    1
		    FROM core_excludefoods excl
		    WHERE excl.food_id = f.food_key
		      AND excl.user_id = pr.user_id
		      AND excl.start_dt <= {week_start_dt} and excl.end_dt >= {week_end_dt}
		  )""".format(**{'user_id':user_id, 'menu_id_list': menu_id_list_str, 
		  	'week_start_dt':"'"+week_start_dt+"'",'week_end_dt':"'"+week_end_dt+"'", 'tag_id_list':tag_id_list_str,'rest_id_list':rest_id_list_str})