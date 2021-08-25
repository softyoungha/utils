/* 현재 켜져있는 세션 확인 */
select * from pg_stat_activity

/* 테이블 락 확인*/
select t.relname,l.locktype,page,virtualtransaction,pid,mode,granted
from pg_locks l, pg_stat_all_tables t
where l.relation=t.relid order by relation asc;

/* pid 프로세스 작업 종료 */
select pg_cancel_backend(160232)

/* pid 세션 강제종료 */
select pg_terminate_backend(14718)


/* DB 지우기 */
-- REVOKE CONNECT ON DATABASE "db_name" FROM exporter;

SELECT pid, pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'db_name' AND pid <> pg_backend_pid()

drop database "db_name"


/* timeout 보기 */
show statement_timeout