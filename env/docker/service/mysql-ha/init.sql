-- password policy
install plugin validate_password soname 'validate_password.so';

SET GLOBAL validate_password_check_user_name=ON;
SET GLOBAL validate_password_dictionary_file='/bitnami/mysql/data/password_dictionary.txt';
SET GLOBAL validate_password_length=8;
SET GLOBAL validate_password_mixed_case_count=1;
SET GLOBAL validate_password_number_count=1;
SET GLOBAL validate_password_policy='STRONG';
SET GLOBAL validate_password_special_char_count=1;


-- grant mars
GRANT ALL PRIVILEGES ON *.* TO 'mars'@'%'

-- create prometheus
CREATE USER 'exporter'@'%' IDENTIFIED BY 'Exporter2020!';

-- grant
GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'%';


-- create mars user
CREATE USER 'marsuser'@'%' IDENTIFIED BY 'Fashion2020!';

-- grant
GRANT ALL PRIVILEGES ON backend.* TO 'marsuser'@'%';


