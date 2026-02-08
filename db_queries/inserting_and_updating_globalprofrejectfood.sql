/* populating globalprobrejectfood */
select 
count(*)
from core_GlobalProbRejectFood
;

INSERT INTO core_GlobalProbRejectFood (food_id,global_star_rating,global_total_uses,prob_r)
(
select
  food_key,
  cast(2.5 as float) as global_star_rating,
  cast(0 as float) as global_total_uses,
  cast(0.85 as decimal(5,4)) as prob_r
 FROM FOOD_FOODS
 )
;
commit;
