
/* meal preferences */
delete
from core_mealpreferences mp_a
  using core_mealpreferences mp_b

where 
  mp_a.id > mp_b.id
  and mp_a.meal_id = mp_b.meal_id;
  
/* food preferences */
select
  prefmenu_id,
  food_id,
  dish_num,
  count(*)
 from core_foodpreferences 
 group by   prefmenu_id, food_id, dish_num
 order by count(*) desc;
 
 select * from core_foodpreferences 
  where prefmenu_id = 1 and food_id = 301818;
/*delete
from core_foodpreferences mp_a
  using core_foodpreferences mp_b

where 
  mp_a.id > mp_b.id
  and mp_a.food_id = mp_b.food_id;*/
  
commit;
