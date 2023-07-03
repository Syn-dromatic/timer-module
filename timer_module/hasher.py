import hashlib
from functools import lru_cache


class Hasher:
    def __init__(self, string: str):
        self.string = string

    @lru_cache(maxsize=128)
    def hash_sha1(self) -> int:
        hasher = hashlib.sha1()
        hasher.update(self.string.encode())
        hash_result = int(hasher.hexdigest(), 16)
        return hash_result
