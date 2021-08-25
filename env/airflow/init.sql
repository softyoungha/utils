-- postgresql backend

CREATE DATABASE airflow;

CREATE USER youngha with ENCRYPTED password 'youngha';

GRANT all privileges on DATABASE airflow to youngha;

GRANT all privileges on all tables in schema public to youngha
