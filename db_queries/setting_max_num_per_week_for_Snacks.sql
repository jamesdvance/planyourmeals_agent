
update core_userprobrejectfood pr set max_num_per_week=10
where pr.food_id in 
(
  select 
     fp.food_id
  from core_prefmenu pm
  join core_foodpreferences fp
    on pm.id = fp.prefmenu_id
    and pm.default_flg = true
    and pm.meal_type in ('Snack', 'Breakfast')
);
commit;
