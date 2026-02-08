select * from auth_user;

select
*
from core_prefmenu
;
select 
*
from core_publicmenu
;

select
*
from core_usermenu;
/* Copying For User = 2 
   Because of the wacky breakfast, lunch, dinner, snack fields, this will never work well for bulk uploads
*/
INSERT INTO core_usermenu (clone_date, breakfast_prefmenu_id, cloned_from_id, dinner_prefmenu_id, lunch_prefmenu_id, snack_prefmenu_id, user_id)
values(null,5, null, 7, 6, 8, 2);
commit;

/* Copying For User=13 */
INSERT INTO core_usermenu (clone_date, breakfast_prefmenu_id, cloned_from_id, dinner_prefmenu_id, lunch_prefmenu_id, snack_prefmenu_id, user_id)
values(null,17, null, 19, 18, 20, 13);
commit;

/* Creating PublicMenus for default */
INSERT INTO core_publicmenu (menu_name, menu_description, total_clones, current_clones, breakfast_prefmenu_id, create_user_id, dinner_prefmenu_id,lunch_prefmenu_id, snack_prefmenu_id)
values('PlanYourMeals Default Menu', 'An American-style healthy diet with plenty of variety for a first time user', 0,0,1,12,3,2,4)
;
commit;

select * from core_usermenu;
