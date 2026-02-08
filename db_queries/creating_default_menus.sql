delete from core_prefmenu;
commit;

/* Creating Default User */
select * from core_profile;
select * from auth_user;

/* Creating Default Menu */
select
* from core_prefmenu;

insert into core_prefmenu  (id, default_flg, menu_name, reusable_flg, public_flg, meal_type, user_id, create_user_id)
values(1, true, 'PlanYourMeals Default Breakfast Menu',true,true,'Breakfast', 12,12); 
commit;

insert into core_prefmenu  (id, default_flg, menu_name, reusable_flg, public_flg, meal_type, user_id, create_user_id)
values(2, true, 'PlanYourMeals Default Lunch Menu',true,true,'Lunch', 12,12); 
commit;

insert into core_prefmenu  (id, default_flg, menu_name, reusable_flg, public_flg, meal_type, user_id, create_user_id)
values(3, true, 'PlanYourMeals Default Dinner Menu',true,true,'Dinner', 12,12); 
commit;

insert into core_prefmenu  (id, default_flg, menu_name, reusable_flg, public_flg, meal_type, user_id, create_user_id)
values(4, true, 'PlanYourMeals Default Snack Menu',true,true,'Snack', 12,12); 
commit;

/* Insert Foods To Menu 
via PSQL
\copy core_foodpreferences (id, meal_type, food_id, dish_num, prefmenu_id)
FROM 'C:/Users/J/Desktop/Businesses/PlanYourMeals.com/Scraped_Data/plm1_default_menu_foods_plm2_menu_ids.csv' CSV HEADER;
*/
select * from core_foodpreferences where prefmenu_id=4;
update core_foodpreferences set dish_num = 'Snacks' where prefmenu_id=4;
commit;

/* Insert FoodTags Menu 
\copy core_foodtagpreferences (id, meal_type,dish_num, tag_id,prefmenu_id)
FROM 'C:/Users/J/Desktop/Businesses/PlanYourMeals.com/Scraped_Data/plm1_default_menu_foodtags_plm2_menu_ids.csv' CSV HEADER;

*/
select * from core_foodtagpreferences;
/* Insert Meals Menu 
\copy core_mealpreferences (id, meal_type,meal_id, dish_num,prefmenu_id)
FROM 'C:/Users/J/Desktop/Businesses/PlanYourMeals.com/Scraped_Data/plm1_default_menu_meals_plm2_menu_ids.csv' CSV HEADER;

*/

select * from core_mealpreferences;
select * from plan_meal where mealname like '%single pan%';

select * from core_prefmenu;

select * from auth_user;
/* Creating jamesishungry menu */
insert into core_prefmenu (id, default_flg, menu_name, reusable_flg, public_flg, meal_type, user_id, create_user_id)
values(5, true, 'jamesishungry Default Breakfast', true, true, 'Breakfast',2,2) ;
commit;
insert into core_prefmenu (id, default_flg, menu_name, reusable_flg, public_flg, meal_type, user_id, create_user_id)
values(6, true, 'jamesishungry Default Lunch', true, true, 'Lunch',2,2) ;
commit;
insert into core_prefmenu (id, default_flg, menu_name, reusable_flg, public_flg, meal_type, user_id, create_user_id)
values(7, true, 'jamesishungry Default Dinner', true, true, 'Dinner',2,2) ;
commit;
insert into core_prefmenu (id, default_flg, menu_name, reusable_flg, public_flg, meal_type, user_id, create_user_id)
values(8, true, 'jamesishungry Default Snack', true, true, 'Snack',2,2) ;
commit;

/**/
select * from core_foodpreferences order by id desc;
ALTER SEQUENCE core_foodpreferences_id_seq RESTART WITH 66;
COMMIT;

/* Copy From Default To my menu */
select * from core_foodpreferences ;
insert into core_foodpreferences (meal_type, dish_num,food_id, prefmenu_id)
(select
  meal_type, 
  dish_num, 
  food_id,
  case 
    when prefmenu_id = 1 then 5 
    when prefmenu_id = 2 then 6 
    when prefmenu_id = 3 then 7 
    when prefmenu_id = 4 then 8 
   else 0  end as prefmenu_id
from core_foodpreferences
);
commit;
/* */
select * from core_mealpreferences;

update core_mealpreferences set id = mod(id,7);

select * from core_mealpreferences order by id desc;
ALTER SEQUENCE core_mealpreferences_id_seq RESTART WITH 80;
COMMIT;

select * from core_mealpreferences ;
insert into core_mealpreferences (meal_type, dish_num,meal_id, prefmenu_id)
(select
  meal_type, 
  dish_num, 
  meal_id,
  case 
    when prefmenu_id = 1 then 5 
    when prefmenu_id = 2 then 6 
    when prefmenu_id = 3 then 7 
    when prefmenu_id = 4 then 8 
   else 0  end as prefmenu_id
from core_mealpreferences);
commit;

/* Food tag preferences */
select * from core_foodtagpreferences order by id desc;
ALTER SEQUENCE core_foodtagpreferences_id_seq RESTART WITH 71;
COMMIT;

select * from core_foodtagpreferences ;
insert into core_foodtagpreferences (meal_type, dish_num,tag_id, prefmenu_id)
(select
  meal_type, 
  dish_num, 
  tag_id,
  case 
    when prefmenu_id = 1 then 5 
    when prefmenu_id = 2 then 6 
    when prefmenu_id = 3 then 7 
    when prefmenu_id = 4 then 8 
   else 0  end as prefmenu_id
from core_foodtagpreferences);
commit;

select
*
from food_restaurants;
select
*
from
food_foodtags;

update core_prefmenu set menu_name = 'Default '||meal_type where user_id =2;
select * from core_prefmenu;

select * from plan_food_amount order by id desc;
ALTER SEQUENCE plan_food_amount_id_seq RESTART WITH 9893;
COMMIT;

select * from core_userprobrejectfood order by id desc;
ALTER SEQUENCE core_userprobrejectfood_id_seq RESTART WITH 447;
COMMIT;
select * from core_userprobrejectmeal order by id desc;
ALTER SEQUENCE core_userprobrejectmeal_id_seq RESTART WITH 465;
COMMIT;
