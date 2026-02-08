select * from auth_user where username in ('james');

delete from core_profile where user_id in (30);
commit;

delete from account_emailaddress where user_id in (30);
commit;

delete from authtoken_token where user_id in (30);
commit;

select id from core_prefmenu where user_id in (30);
delete from core_foodtagpreferences where prefmenu_id in (93,94,95,96);
commit;
delete from core_foodpreferences where prefmenu_id in (93,94,95,96);
commit;
delete from core_mealpreferences where prefmenu_id in (93,94,95,96);
commit;


delete from core_usermenu where user_id in (30);
commit;
delete from core_prefmenu where user_id in (30);
commit;

delete from core_personalprofile where user_id in (30);
commit;

delete from core_UserAccount where user_id in (30);
commit;

select * from plan_food_amount fa join plan_meal m on fa.meal_id = m.id where m.user_id=30;
-- this user account created a bunch of meals. f.

delete from plan_meal where user_id in (30);
commit;

select * from plan_food_amount;

delete from plan_planmeal where user_id in (30);
commit;

delete from auth_user where id in (30);
commit;
