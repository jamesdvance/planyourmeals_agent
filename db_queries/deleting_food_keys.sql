select * from food_foods where food_description like '%julie%'; -- 473068

select distinct added_by_id from food_recipes;

select * from food_recipes where food_id = 473096;

select * from food_Foods where food_key = (select max(food_key) from food_foods);
select * from food_recipefood limit 10;
-- 473096
delete from food_recipefood where recipe_id = 473096;
commit;
delete from food_recipes where food_id = 473096;
commit;
delete from food_altservingsize where food_id = 473096;
commit;
delete from food_foodindex where food_id = 473096;
commit;
delete from core_GlobalProbRejectFood where food_id=473096;
commit;
delete from food_foods where food_key = 473096;
commit;


select * from food_recipefood order by id desc;
ALTER SEQUENCE food_recipefood_id_seq RESTART WITH 25898;
COMMIT;

select * from food_recipes limit 10;
