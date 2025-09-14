from contextlib import contextmanager
from .db_routers import UsePrimaryReads


@contextmanager
def use_primary_reads():
    with UsePrimaryReads():
        yield

