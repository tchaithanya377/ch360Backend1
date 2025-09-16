from rest_framework.pagination import CursorPagination


class DefaultCursorPagination(CursorPagination):
    """Global cursor pagination with a safe default ordering.

    DRF's default uses "-created" which many models don't have.
    We standardize on "-created_at" which is widely present across models.
    """

    ordering = '-created_at'


