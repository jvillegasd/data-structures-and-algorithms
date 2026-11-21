# https://www.fastprep.io/problems/tiktok-lru-cache-with-ttl-expiration
# https://medium.com/@muzhou1994/implementation-of-lru-cache-with-an-expiry-time-for-each-entry-bbe77b5c8a7e

"""LRU Cache + TTL on each key
This is my implementation of a LRU cache with TTL on each key. The main idea is to set an expiration
time on the key we store in our cache. Now, we have two cases on evict / remove items:
    -   On expired key
    -   On least recently used key

On this kind of LRU cache, we first aim to evict the expired keys before removing de LRU keys.
On this implementation I considered to use `time.time()` to make all time calculations in `ms`. Also,
this implementation uses an hibryd lazy deletion.

What does this "hybrid lazy deletion" means?

A full lazy deletion is that you only remove expired keys when they are consulted. The trade-off are:
    -   `put` does not cleanup, expired keys may grow in memory
    -   `put` may remove an active lru key before an expired key near to head

What I did here is to add a cleanup of expired keys in `put` and the trade-off here is when cache reached capacity,
the method will have time complexity O(n) since needs to loop the cache.

Another to do this cleanup would be to actively clean the expired keys by using a background job or thread.
"""

import time
from collections import OrderedDict
from unittest.mock import patch


def now_in_ms() -> int:
    return int(time.time() * 1000)


class LRUCacheWithTTL:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()

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
        self.cache[key] = {"value": value, "expires_at_ms": now_ms + ttl_ms}
        self.cache.move_to_end(key)

        if len(self.cache) <= self.capacity:
            return

        # Evict / remove the oldest expired key
        for key, value in self.cache.items():
            if value["expires_at_ms"] <= now_ms:
                del self.cache[key]
                return

        # If there is not expired keys, fallback to LRU item
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
    [2, 20, 5],  # t=1001: key 2 expires at 1006
    [2],  # t=1006: still valid at its exact deadline
    [3, 30, 50],  # t=1007: evicts expired key 2, even though 1 is LRU
    [2],  # miss
    [1],  # hit: key 3 is now LRU
    [4, 40, 50],  # both entries are live, so evict key 3
    [3],  # miss
    [1, 99, 200],  # update key 1's value and extend its deadline to 1212
    [1],  # t=1101: past the original deadline, returns 99
    [1],  # t=1212: still valid at the new deadline
    [1],  # t=1213: expired
]
times_ms = [1000, 1001, 1005, 1007, 1008, 1009, 1010, 1011, 1012, 1101, 1212, 1213]
expected = [
    None,  # put(1)
    None,  # put(2)
    20,    # t=1005: key 2 is live until 1006
    None,  # t=1007: put(3) evicts expired key 2
    -1,    # key 2 is gone
    10,    # key 1 survived and becomes most recently used
    None,  # put(4) evicts live LRU key 3
    -1,    # key 3 is gone
    None,  # update key 1 to 99 with a new deadline of 1212
    99,    # t=1101: key 1 is live under its extended TTL
    -1,    # t=1212: key 1 expires at its exact deadline
    -1,    # t=1213: key 1 is gone
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
