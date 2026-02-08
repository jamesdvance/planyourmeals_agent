
/* Done without trigrams */

/*CREATE INDEX gin_food_desc ON food_foods USING gin(food_description text)*/

select * from pg_available_extensions;
--CREATE EXTENSION gin_trgm_ops;
CREATE EXTENSION pg_trgm;
/*Done with trigrams */
CREATE INDEX gin_tg_food_desc ON food_foods USING gin(food_description gin_trgm_ops);

CREATE INDEX gin_tg_brand ON food_foods USING gin(brand gin_trgm_ops);

CREATE INDEX gin_tg_restaurant ON food_restaurants USING gin(restaurant gin_trgm_ops);

CREATE INDEX gin_food_tag on food_foodtags USING gin(name gin_trgm_ops);


