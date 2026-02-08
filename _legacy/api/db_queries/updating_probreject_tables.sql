

select
*
from core_UserProbRejectMeal;

select
*
from core_UserProbRejectFood;

SELECT
*FROM FOOD_FOODS WHERE FOOD_KEY > 473000 ORDER BY FOOD_KEY DESC;


/*
PSQL - 
\copy core_userprobrejectfood (id, viewed, removed, food_id,user_id,dislike_ind,last_view, max_servings) 
from 'C:/Users/J/Desktop/Businesses/PlanYourMeals.com/Scraped_Data/plm1_userprobrejectfood_updated_ids.csv' CSV HEADER;

*/
/* Update Ids */
select * from core_userprobrejectmeal order by id desc;
ALTER SEQUENCE core_userprobrejectmeal_id_seq RESTART WITH 465;
COMMIT;
