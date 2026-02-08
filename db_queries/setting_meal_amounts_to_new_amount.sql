
/* Updating food amount's amount and amount divisor to reflect the system: 

Amount: the amount in the units indexed by serving size index
Amount divisor: The original serving size val indexed by serving size index. After dividing by this, the amount leftover is the same as the same old "food amount"

if the amount is 12 oz, and the serving size index is 0 and the 0th serving size amount is 4, amount divisor is 4. 
To get the calories for this amount, one would multiply the number of calories times (the amount divided by the amount divisor)
 */

update plan_food_amount am
set 
  amt = s.amt * s.serving_size_val,
  amount_divisor = s.serving_size_val

from 
  (
  select
  *
  from    
  plan_food_amount am
  join food_foods f
    on am.food_id = f.food_key) s
    
where am.serving_size_idx = 0
and am.id = s.id
  ;
  
SELECT * FROM PLAN_FOOD_AMOUNT;
  
 commit;
 
