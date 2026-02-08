

/* Don't create a user in SQL, create it from the Django shell */
/* JWT expects passwords to be hashed before storing */
update auth_user
set email = 'james.dvance@gmail.com'
where id =1;
commit;

update auth_user
set password = '123'
where id =1;
commit;

