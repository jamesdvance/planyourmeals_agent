

select
food_key,
food_description,
brand,
food_type_grp,
serving_size_unit,
serving_size_val
from food_foods

where image_url = 'https://planyourmealsmedia.s3.amazonaws.com/food/default_thumbnail.png' 
and food_description like '%gtin%';

select
substring(food_description,1, position('unprepared, gtin' in food_description)-3)
from 
food_foods
where food_description like '%unprepared, gtin%';

select
case when 
  right(substring(food_description,1, position('prepared, gtin' in food_description)-3),1) in (',','|','.','"','/')
  then left(substring(food_description,1, position('prepared, gtin' in food_description)-3), length(substring(food_description,1, position('prepared, gtin' in food_description)-3))-1)
  else substring(food_description,1, position('prepared, gtin' in food_description)-3)
  end 
from 
food_foods
where food_description like '%prepared, gtin%';

update 
food_foods
set food_description = substring(food_description, 
where food_description like '%gtin%'
