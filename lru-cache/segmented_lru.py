"""Segmented LRU Cache

This is my implementation of segmented LRU cache. This variant of LRU cache consit of moving keys between 2 or 3
states: (Hot, Warm, Cold). In this case, I will use only Hot and Cold states for simplicity.

When I read about this variant, the criteria used to move keys back and forth between states depends on your use,
someones only promote when key is hit on `get`. In my case, I will promove when key is hit either `get` or `put`.

But, when we `put` a new key in the cache, we always insert it in the cold cache, hot cache is for frequent keys.
"""


from collections import OrderedDict


class SegmentedLRUCache:

    def __init__(self, hot_capacity: int, cold_capacity: int):
        self.hot_capacity = hot_capacity
        self.cold_capacity = cold_capacity
        self.hot_cache = OrderedDict()
        self.cold_cache = OrderedDict()

    def _promote(self, key: str, value: int):
        if len(self.hot_cache) >= self.hot_capacity:
            demoted_key, demoted_value = self.hot_cache.popitem(last=False)
            if len(self.cold_cache) >= self.cold_capacity:
                self.cold_cache.popitem(last=False)

            self.cold_cache[demoted_key] = demoted_value
            self.cold_cache.move_to_end(demoted_key)

        self.hot_cache[key] = value
        self.hot_cache.move_to_end(key)

    def get(self, key: str) -> int:
        if key in self.hot_cache:
            self.hot_cache.move_to_end(key)
            return self.hot_cache[key]

        if key in self.cold_cache:
            value = self.cold_cache.pop(key)
            self._promote(key, value)
            return value

        return -1

    def put(self, key: str, value: int) -> None:
        if key in self.hot_cache:
            self.hot_cache[key] = value
            self.hot_cache.move_to_end(key)
            return

        if key in self.cold_cache:
            del self.cold_cache[key]
            self._promote(key, value)
            return

        if len(self.cold_cache) >= self.cold_capacity:
            self.cold_cache.popitem(last=False)

        self.cold_cache[key] = value
        self.cold_cache.move_to_end(key)



hot_capacity = 3
cold_capacity = 3
obj = SegmentedLRUCache(hot_capacity, cold_capacity)

ops_l = [
    "put", "put", "put", "put", "put",
    "get", "get", "get",
    "put", "get", "put", "get",
    "get", "get", "put", "get",
    "get", "get", "get",
]
ops_args = [
    ["A", 10],
    ["B", 20],
    ["C", 30],
    ["D", 40],
    ["E", 50],
    ["A"],
    ["B"],
    ["C"],
    ["F", 60],
    ["D"],
    ["A", 100],
    ["A"],
    ["E"],
    ["F"],
    ["G", 70],
    ["G"],
    ["B"],
    ["C"],
    ["D"],
]
expected = [
    None, None, None, None, None,
    -1, -1, 30,
    None, 40, None, 100,
    50, 60, None, 70,
    -1, 30, 40,
]
ops = [
    {"op": op, "args": args}
    for op, args in zip(ops_l, ops_args)
]
results = []

for item in ops:
    method = getattr(obj, item["op"])
    results.append(method(*item["args"]))

print(results)
assert results == expected, (results, expected)
