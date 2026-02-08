

CREATE TABLE core_probrejectfoodcoefficients (
  item_type varchar(4),
  viewed float,
  removed float,
  stars float,
  total_uses float,
  last_view float,
  last_use float
);
commit;

CREATE TABLE core_probrejectmealcoefficients (
  item_type varchar(4),
  viewed float,
  removed float,
  total_uses float,
  last_view float,
  last_use float
);
commit;

ALTER TABLE core_probrejectfoodcoefficients 
DROP COLUMN last_use;
commit;

ALTER TABLE core_probrejectmealcoefficients 
DROP COLUMN last_use;
commit;
