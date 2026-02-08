
select 
distinct 
serving_size_idx
from plan_food_amount;

update plan_food_amount am
set amount_divisor = (f.serving_sizes -> 'ss_amts' ->> am.serving_size_idx)::float
FROM food_altservingsize f
WHERE am.food_id = f.food_id;
commit;

/* Check */
select
*
from plan_food_amount F
join food_altservingsize A
  ON F.FOOD_ID = A.FOOD_ID
where amount_divisor is not null
limit 100;

