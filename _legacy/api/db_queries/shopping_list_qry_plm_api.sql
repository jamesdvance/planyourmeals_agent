
SELECT
	  id,
	  food_description,
	  serving_size_unit,
	  sum(total_amount) as total_amount
  FROM
    (
    SELECT
      w.user_id as id,
      f.food_description,
      REPLACE(CAST(alt.serving_sizes->'ss_units'->am.serving_size_idx as varchar(30)),'"','') as serving_size_unit,
      am.amt as total_amount
    FROM plan_planmeal w
    JOIN plan_meal m
      ON w.meal_id = m.id
    JOIN plan_food_amount am
      ON (m.id = am.meal_id)
    JOIN food_foods f
      ON (am.food_id = f.food_key
          AND f.food_type_grp in ('grocery','raw_ingredient'))
    JOIN food_altservingsize alt
      ON f.food_key = alt.food_id
    WHERE w.user_id = 2 AND w.plan_date >= '2020-01-17' AND w.plan_date <= '2020-01-23'
    UNION ALL
    SELECT 
      w.user_id as id,
      r.ingred_food_desc as food_description,
      r.ingred_serving_size_unit as serving_size_unit,
      r.ingred_amt as total_amount
    FROM plan_planmeal w
    JOIN plan_meal m
      ON  w.meal_id = m.id
    JOIN plan_food_amount am
      ON (m.id = am.meal_id)
    JOIN food_foods f
      ON (am.food_id = f.food_key
          AND f.food_type_grp IN ('recipe'))     
    JOIN food_recipefood r 
      ON (f.food_key = r.recipe_id)
    WHERE w.user_id = 2  AND w.plan_date >= '2020-01-17' AND w.plan_date <= '2020-01-23'
    ) food_amounts
    GROUP BY food_description, serving_size_unit, id
ORDER BY food_description
