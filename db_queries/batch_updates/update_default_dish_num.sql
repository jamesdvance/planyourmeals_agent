
UPDATE food_foods set
  default_dish_num = subquery.default_dish_num
FROM(
SELECT
  food_id, 
  default_dish_num
FROM(
SELECT
  food_id,
  default_dish_num,
  row_number() over(partition by food_id||default_dish_num order by total desc) as row_num
FROM (
    SELECT 
      food_id,
      default_dish_num,
      count(*) AS TOTAL
    FROM (
      SELECT
        food_id,
        dish_num as default_dish_num
       FROM core_foodpreferences
      UNION
      SELECT
        food_id,
        default_dish_num
       FROM 
        core_userprobrejectfood
    ) bar
    GROUP BY food_id,default_dish_num
  ) as foo
) as bar
WHERE row_num =1
) subquery

WHERE food_foods.food_key = subquery.food_id;
