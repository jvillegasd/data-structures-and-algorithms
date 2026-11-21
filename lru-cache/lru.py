from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1

        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: int, value: int) -> None:
        if key not in self.cache and len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)

        if key in self.cache:
            self.cache.move_to_end(key)

        self.cache[key] = value


capacity = 2
obj = LRUCache(capacity)
ops_l = ["put", "put", "get", "put", "get", "put", "get", "get", "get"]
ops_args = [[1, 1], [2, 2], [1], [3, 3], [2], [4, 4], [1], [3], [4]]
ops = [{"op": op, "args": args} for op, args in zip(ops_l, ops_args)]
results = []

for item in ops:
    method = getattr(obj, item["op"])
    ans = method(*item["args"])
    results.append(ans)

print(results)
