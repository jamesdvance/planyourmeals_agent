
update auth_user
set is_staff = true
where username='james.dvance@gmail.com'
;
commit;
select * from auth_user;

select * from auth_user where username= 'test8';

delete from account_emailaddress
where email ='test230498@gmail.com';
commit;

delete from authtoken_token
where user_id = 10;
commit;

delete from auth_user
where username='test8';
commit;
