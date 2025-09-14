import time
from typing import Callable, Any, Dict, List

from django.utils.deprecation import MiddlewareMixin
from django_redis import get_redis_connection
from django.core.cache import cache
from django.db import connections


def _now_seconds() -> int:
    return int(time.time())


def _redis() -> Any:
    try:
        return get_redis_connection("default")
    except Exception:
        return None


def record_rps() -> None:
    ts = _now_seconds()
    r = _redis()
    key = f"metrics:rps:{ts}"
    if r is not None:
        r.incr(key, 1)
        r.expire(key, 120)
    else:
        cache_key = key
        try:
            cache.incr(cache_key)
        except Exception:
            cache.set(cache_key, 1, 120)


def push_latency(key: str, ms: float, max_len: int = 5000) -> None:
    r = _redis()
    list_key = f"metrics:{key}:latencies"
    if r is not None:
        r.lpush(list_key, f"{ms:.3f}")
        r.ltrim(list_key, 0, max_len - 1)
        r.expire(list_key, 3600)
    else:
        # Fallback: keep rolling sample in cache
        sample: List[float] = cache.get(list_key) or []
        sample.insert(0, ms)
        if len(sample) > max_len:
            sample = sample[:max_len]
        cache.set(list_key, sample, 3600)


def get_rps_window(window_seconds: int = 60) -> float:
    now = _now_seconds()
    r = _redis()
    total = 0
    for t in range(now - window_seconds + 1, now + 1):
        key = f"metrics:rps:{t}"
        if r is not None:
            val = r.get(key)
            total += int(val or 0)
        else:
            val = cache.get(key)
            total += int(val or 0)
    return total / float(window_seconds)


def _compute_percentiles(values: List[float], percentiles: List[float]) -> Dict[str, float]:
    if not values:
        return {f"p{int(p*100)}": 0.0 for p in percentiles}
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    results: Dict[str, float] = {}
    for p in percentiles:
        if n == 1:
            idx = 0
        else:
            idx = min(n - 1, max(0, int(round(p * (n - 1)))))
        results[f"p{int(p*100)}"] = float(sorted_vals[idx])
    return results


def get_latency_percentiles(key: str, percentiles: List[float]) -> Dict[str, float]:
    r = _redis()
    list_key = f"metrics:{key}:latencies"
    values: List[float] = []
    if r is not None:
        try:
            raw = r.lrange(list_key, 0, 4999)
            values = [float(x) for x in raw]
        except Exception:
            values = []
    else:
        values = cache.get(list_key) or []
    return _compute_percentiles(values, percentiles)


class MetricsMiddleware(MiddlewareMixin):
    """Records per-request metrics: RPS, request latency, and DB latency percentiles.

    - RPS: increments a per-second counter
    - Request latency: wall clock from view start to response end
    - DB latency: sums SQL execution time per request using execute_wrapper
    """

    def process_view(self, request, view_func: Callable, view_args, view_kwargs):
        request._metrics_start = time.perf_counter()
        request._db_time_ms = 0.0

        def wrapper_execute(execute, sql, params, many, context):
            start = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                request._db_time_ms += elapsed_ms

        # Wrap default connection for the duration of the request
        request._execute_wrapper_cm = connections["default"].execute_wrapper(wrapper_execute)
        request._execute_wrapper_cm.__enter__()
        return None

    def process_response(self, request, response):
        try:
            record_rps()
            if hasattr(request, "_metrics_start"):
                req_ms = (time.perf_counter() - request._metrics_start) * 1000.0
                push_latency("request", req_ms)
                db_ms = getattr(request, "_db_time_ms", 0.0)
                push_latency("db", db_ms)
        finally:
            cm = getattr(request, "_execute_wrapper_cm", None)
            if cm is not None:
                try:
                    cm.__exit__(None, None, None)
                except Exception:
                    pass
        return response


def collect_app_metrics() -> Dict[str, Any]:
    rps_1m = get_rps_window(60)
    req_p = get_latency_percentiles("request", [0.5, 0.9, 0.95, 0.99])
    db_p = get_latency_percentiles("db", [0.5, 0.9, 0.95, 0.99])
    return {
        "rps_60s": round(rps_1m, 2),
        "request_ms": req_p,
        "db_ms": db_p,
        "sample_sizes": {
            # Provide rough visibility into sample windows
            "request": len(cache.get("metrics:request:latencies") or []),
            "db": len(cache.get("metrics:db:latencies") or []),
        },
    }


