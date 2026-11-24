"""LRU Cache + TTL on each key + Min-heap

The main implementation of this LRU case is the same addressed in `lru-cache/lru_ttl_each_item.py` but the new
change here is instead of evicting the oldest expired key iteratively (time complexity O(n)), we will use another
data structure called Heap. In our case we are interesed to keep the oldest expired key and since we normalized dates
by using them with milliseconds, the oldest expired key is always minimum milliseconds value, so we will implement
the Min-heap. A Min-Heap, allow us to have the minimum value at root and greater value than root as children.

By having a Min-heap will reduce time complexity of `put` from O(n) to O(log(n)) amortized when cache is full.

What `amortized` means?

`put` will be pushing `expires_at_ms` time onto the heap, even when it updates an existing key. That means that we can
have several nodes in the heap. So whenever we reach a threshould we will rebuild the heap with current `expires_at_ms`
in linear time. This is the trade-off I accept to keep hybrid lazy deletion as fast as possible.
"""

import heapq
import time
from collections import OrderedDict
from unittest.mock import patch


def now_in_ms() -> int:
    return int(time.time() * 1000)


class LRUCacheWithTTL:

    HEAP_THRESHOLD: int = 2

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.min_heap = []

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1

        if self.cache[key]["expires_at_ms"] <= now_in_ms():
            del self.cache[key]
            return -1

        self.cache.move_to_end(key)
        return self.cache[key]["value"]

    def put(self, key: int, value: int, ttl_ms: int) -> None:
        now_ms = now_in_ms()
        expires_at_ms = now_ms + ttl_ms

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

    def _evict(self, now_ms: int) -> None:
        # Evict expired keys first
        while self.min_heap and self.min_heap[0][0] <= now_ms:
            expires_at_ms, key = heapq.heappop(self.min_heap)

            is_key_not_refreshed_in_cache = (
                key in self.cache and
                self.cache[key]["expires_at_ms"] == expires_at_ms
            )
            if is_key_not_refreshed_in_cache:
                del self.cache[key]
                return

        # Cache only has live keys, evict LRU key
        self.cache.popitem(last=False)



capacity = 2
obj = LRUCacheWithTTL(capacity)

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
    [1, 10, 100],  # t=1000: key 1 expires at 1100
    [2, 20, 5],    # t=1001: key 2 expires at 1006
    [2],           # t=1005: key 2 is live one millisecond before expiry
    [3, 30, 50],   # t=1006: evict key 2 at its exact deadline; key 1 survives
    [2],           # t=1008: miss
    [1],           # t=1009: hit, making key 3 the LRU
    [4, 40, 50],   # t=1010: both existing entries are live, so evict key 3
    [3],           # t=1011: miss
    [1, 99, 200],  # t=1012: update key 1's value and extend its deadline to 1212
    [1],           # t=1101: past the original deadline, returns 99
    [1],           # t=1212: key 1 expires at its exact deadline
    [1],           # t=1213: key 1 is gone
]
times_ms = [1000, 1001, 1005, 1006, 1008, 1009, 1010, 1011, 1012, 1101, 1212, 1213]
expected = [
    None,  # put(1)
    None,  # put(2)
    20,    # get(2) just before expiry
    None,  # put(3) at key 2's deadline
    -1,    # key 2 is gone
    10,    # live LRU key 1 survived the expiry eviction
    None,  # put(4) evicts key 3
    -1,    # key 3 is gone
    None,  # update key 1
    99,    # key 1 is live under its extended TTL
    -1,    # exact-deadline miss
    -1,    # repeated miss
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
