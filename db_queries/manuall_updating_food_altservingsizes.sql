/* Getting all that need to be inserted */
select
f.food_key,
s.food_id
from food_foods f
left join food_altservingsize s
  on f.food_key = s.food_id
where s.food_id is null
order by f.food_key ;

insert into food_altservingsize 
select
f.food_key as food_id,
'{"ss_amts":[1.0],"ss_units":["serving"]}' as serving_sizes
from food_foods f
left join food_altservingsize s
  on f.food_key = s.food_id
where s.food_id is null;

commit;



