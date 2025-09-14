## Database Scaling Guide

### 1) pgBouncer
Use transaction pooling for Django or session pooling if you need per-connection features.

Update env:
```
DATABASE_URL=postgres://user:pass@pgbouncer-host:6432/dbname
```
Set in Django:
```
CONN_MAX_AGE=0  # for transaction pooling
```

### 2) Indexes and Partitioning
Run:
```
python manage.py optimize_database
python manage.py optimize_attendance_db
python manage.py optimize_assignments_db
```
Partition high-volume tables (time-based): audit logs, attendance, submissions.
Implement via SQL migrations creating a parent table and monthly partitions.

### 3) pg_stat_statements
Postgres:
```
shared_preload_libraries = 'pg_stat_statements'
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```
Export slow queries:
```
python manage.py export_slow_queries --limit 50 > slow-queries.json
```

### 4) Security: TLS + SCRAM
Set `ssl=on`, `password_encryption=scram-sha-256`, update `pg_hba.conf` to `hostssl ... scram-sha-256`.
Rotate app and pgBouncer user passwords.

### 5) pgaudit + Logging
```
shared_preload_libraries = 'pg_stat_statements,pgaudit'
CREATE EXTENSION IF NOT EXISTS pgaudit;
```
Ship logs to central store (ELK/CloudWatch/Datadog).

### 6) Backups + WAL Shipping
Use wal-g or pgBackRest. Test restore regularly.

### 7) RLS
Enable in settings: `ENABLE_RLS=true`.
Apply:
```
python manage.py apply_rls
```
Gateway middleware sets `app.current_department` from `X-Department-ID`.

### 8) Monitoring & Alerts
Scrape `/metrics` (django-prometheus), Postgres exporter, Redis exporter, pgBouncer exporter.
Alert on latency p95/p99, error rates, saturation, replication lag, cache hit ratio.


