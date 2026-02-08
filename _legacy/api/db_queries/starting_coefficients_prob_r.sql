
--DELETE FROM core_probrejectcoefficients;
--COMMIT;

INSERT INTO core_probrejectcoefficients (item_type, keep_ratio,days_since_view, days_since_use,random_var, inv_stars_mult)
VALUES('food', 0.3, 0.1, 0.25, 0.05, 0.3);
commit;

INSERT INTO core_probrejectcoefficients (item_type, keep_ratio,days_since_view, days_since_use,random_var, inv_stars_mult)
VALUES('meal', 0.3, 0.1, 0.25, 0.05, 0.3);
commit;

UPDATE  core_probrejectcoefficients SET inv_total_uses=0.3;
COMMIT;
