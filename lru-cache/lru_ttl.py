# https://jamesg.blog/2024/08/18/time-based-lru-cache-python
"""LRU Cache + TTL + Min-heap

This is another variant with TTL + Min-heap for cleanup, this time the same TTL is applied in all keys
"""

import heapq
import time
from collections import OrderedDict
from unittest.mock import patch


def now_in_ms() -> int:
    return int(time.time() * 1000)


class LRUCacheWithTTL:

    HEAP_THRESHOLD: int = 2

    def __init__(self, capacity: int, ttl_ms: int):
        self.capacity = capacity
        self.ttl_ms = ttl_ms
        self.cache = OrderedDict()
        self.min_heap = []

    def _evict(self, now_ms: int) -> None:
        while self.min_heap and self.min_heap[0][0] <= now_ms:
            expires_at_ms, key = heapq.heappop(self.min_heap)

            is_key_not_refreshed_in_cache = (
                key in self.cache and
                self.cache[key]["expires_at_ms"] == expires_at_ms
            )
            if is_key_not_refreshed_in_cache:
                del self.cache[key]
                return

        # Cache only has live items, evict LRU
        self.cache.popitem(last=False)

    def get(self, key: str) -> int:
        if key not in self.cache:
            return -1

        if self.cache[key]["expires_at_ms"] <= now_in_ms():
            del self.cache[key]
            return -1

        self.cache.move_to_end(key)
        return self.cache[key]["value"]

    def put(self, key: str, value: int) -> None:
        now_ms = now_in_ms()
        expires_at_ms = now_ms + self.ttl_ms

        self.cache[key] = {"value": value, "expires_at_ms": expires_at_ms}
        self.cache.move_to_end(key)
        heapq.heappush(self.min_heap, (expires_at_ms, key))

        if len(self.cache) > self.capacity:
            self._evict(now_ms)

        # Rebuild min-heap to keep memory usage
        if len(self.min_heap) > self.HEAP_THRESHOLD * self.capacity:
            self.min_heap = [
                (value["expires_at_ms"], key)
                for key, value in self.cache.items()
            ]
            heapq.heapify(self.min_heap)



capacity = 2
obj = LRUCacheWithTTL(capacity, ttl_ms=5)

ops_l = [
    "put",
    "put",
    "get",
    "put",
    "get",
    "get",
    "put",
    "get",
    "put",
    "get",
    "get",
    "get",
]
ops_args = [
    [1, 10],  # t=1000: key 1 expires at 1005
    [2, 20],  # t=1001: key 2 expires at 1006
    [2],      # t=1005: key 2 is still live
    [3, 30],  # t=1006: evict expired key 1
    [2],      # t=1008: key 2 has expired
    [1],      # t=1009: key 1 is gone
    [4, 40],  # t=1010: key 3 and key 4 are live
    [3],      # t=1011: key 3 expires at its deadline
    [1, 99],  # t=1012: insert key 1 again
    [1],      # t=1016: key 1 is still live
    [1],      # t=1017: key 1 expires at its deadline
    [1],      # t=1018: key 1 is gone
]
times_ms = [
    1000, 1001, 1005, 1006,
    1008, 1009, 1010, 1011,
    1012, 1016, 1017, 1018,
]
expected = [
    None,
    None,
    20,
    None,
    -1,
    -1,
    None,
    -1,
    None,
    99,
    -1,
    -1,
]
ops = [
    {"op": op, "args": args, "time": t}
    for op, args, t in zip(ops_l, ops_args, times_ms)
]

results = []

with patch(f"{LRUCacheWithTTL.__module__}.now_in_ms") as clock:
    for item in ops:
        clock.return_value = item["time"]

        method = getattr(obj, item["op"])
        results.append(method(*item["args"]))

print(results)
assert results == expected, (results, expected)
