/*
Didn't do this because some image searches failed
update food_foods
set image_url =  concat('https://planyourmealsmedia.s3.amazonaws.com/food/', food_key,'/thumbnail.png');
commit;
*/
update food_foods
set image_url = 'https://planyourmealsmedia.s3.amazonaws.com/food/default_thumbnail.png';
commit;

select * 
from food_foods
limit 10;
