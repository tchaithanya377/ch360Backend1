class ReadReplicaRouter:
    def db_for_read(self, model, **hints):
        # Allow forcing primary reads via hint or thread-local flag
        force_primary = hints.get('force_primary') or getattr(ReadReplicaRouter, '_force_primary', False)
        return 'default' if force_primary else 'read_replica'

    def db_for_write(self, model, **hints):
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == 'default'


class UsePrimaryReads:
    def __enter__(self):
        ReadReplicaRouter._force_primary = True
        return self

    def __exit__(self, exc_type, exc, tb):
        ReadReplicaRouter._force_primary = False
        return False

