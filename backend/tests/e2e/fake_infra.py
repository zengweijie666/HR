"""
文件名: tests/e2e/fake_infra.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 端到端测试用的内存版 MongoDB/Redis，模拟 motor 异步行为
入参: 无
出参: FakeCollection / FakeMongoDB / FakeRedis 类

设计要点：
- motor find()/aggregate() 同步返回 cursor，to_list() 为协程
- update_one 的 update 通过关键字参数 update= 传递
- 支持 $set / $push / $each / $slice / $in / $gte / $lte / $regex / $or 等操作符
- 数据在内存 list 中流转，使多 API 调用能共享状态
"""
from unittest.mock import MagicMock


def _get_nested(doc: dict, key: str):
    """支持 dotted key: basic_info.name"""
    if not isinstance(doc, dict):
        return None
    val = doc
    for part in str(key).split("."):
        if isinstance(val, dict):
            val = val.get(part)
        else:
            return None
        if val is None:
            return None
    return val


def _set_nested(doc: dict, key: str, value):
    """设置 dotted key"""
    parts = str(key).split(".")
    d = doc
    for p in parts[:-1]:
        if p not in d or not isinstance(d[p], dict):
            d[p] = {}
        d = d[p]
    d[parts[-1]] = value


def _match_query(doc: dict, query: dict) -> bool:
    """简化 MongoDB 查询匹配，支持常用操作符"""
    if not query:
        return True
    for k, v in query.items():
        if k == "$or":
            if not any(_match_query(doc, cond) for cond in v):
                return False
        elif k == "$and":
            if not all(_match_query(doc, cond) for cond in v):
                return False
        else:
            doc_val = _get_nested(doc, k)
            if isinstance(v, dict):
                for op, op_val in v.items():
                    if op == "$gte" and not (doc_val is not None and doc_val >= op_val):
                        return False
                    elif op == "$lte" and not (doc_val is not None and doc_val <= op_val):
                        return False
                    elif op == "$gt" and not (doc_val is not None and doc_val > op_val):
                        return False
                    elif op == "$lt" and not (doc_val is not None and doc_val < op_val):
                        return False
                    elif op == "$in" and doc_val not in op_val:
                        return False
                    elif op == "$regex":
                        if not doc_val or str(op_val) not in str(doc_val):
                            return False
                    elif op == "$ne":
                        if doc_val == op_val:
                            return False
            else:
                if doc_val != v:
                    return False
    return True


def _apply_update(doc: dict, update: dict):
    """应用 $set / $push 操作"""
    if "$set" in update:
        for k, v in update["$set"].items():
            _set_nested(doc, k, v)
    if "$push" in update:
        for k, v in update["$push"].items():
            arr = _get_nested(doc, k) or []
            if not isinstance(arr, list):
                arr = []
            if isinstance(v, dict) and "$each" in v:
                arr.extend(v["$each"])
                if "$slice" in v:
                    sl = v["$slice"]
                    arr = arr[sl:] if sl < 0 else arr[:sl]
            else:
                arr.append(v)
            _set_nested(doc, k, arr)


class FakeCursor:
    """模拟 motor cursor：同步链式调用 + 异步 to_list"""

    def __init__(self, data: list):
        self._data = list(data)

    def sort(self, key, direction=1):
        reverse = direction == -1
        self._data.sort(key=lambda x: _get_nested(x, key) or "", reverse=reverse)
        return self

    def skip(self, n):
        self._data = self._data[n:]
        return self

    def limit(self, n):
        self._data = self._data[:n]
        return self

    async def to_list(self, length=None):
        return list(self._data[:length] if length else self._data)


class FakeCollection:
    """模拟 motor collection：内存存储 + 异步方法"""

    def __init__(self, name: str = ""):
        self.name = name
        self._data: list[dict] = []

    async def insert_one(self, doc: dict):
        import copy
        self._data.append(copy.deepcopy(doc))
        result = MagicMock()
        result.inserted_id = str(len(self._data))
        return result

    async def find_one(self, query=None, projection=None):
        import copy
        query = query or {}
        for doc in self._data:
            if _match_query(doc, query):
                return copy.deepcopy(doc)
        return None

    def find(self, query=None, projection=None):
        import copy
        query = query or {}
        matched = [copy.deepcopy(d) for d in self._data if _match_query(d, query)]
        return FakeCursor(matched)

    async def count_documents(self, query=None):
        query = query or {}
        return sum(1 for d in self._data if _match_query(d, query))

    async def update_one(self, query, update=None, upsert=False, **kwargs):
        # 兼容 update 作为关键字参数传递
        if update is None:
            update = kwargs.get("update", {})
        query = query or {}
        for doc in self._data:
            if _match_query(doc, query):
                _apply_update(doc, update)
                return MagicMock(modified_count=1, matched_count=1)
        if upsert:
            import copy
            new_doc = {}
            _apply_update(new_doc, update)
            self._data.append(new_doc)
            return MagicMock(modified_count=0, matched_count=0, upserted_id="upserted")
        return MagicMock(modified_count=0, matched_count=0)

    async def delete_one(self, query):
        query = query or {}
        for i, doc in enumerate(self._data):
            if _match_query(doc, query):
                self._data.pop(i)
                return MagicMock(deleted_count=1)
        return MagicMock(deleted_count=0)

    def aggregate(self, pipeline):
        """简化聚合：top_skills / education / salary 分布返回空列表（e2e 测试不依赖聚合）"""
        return FakeCursor([])


class FakeMongoDB:
    """模拟 MongoDB 数据库，各 collection 用内存 list 存储"""

    def __init__(self):
        self.resumes = FakeCollection("resumes")
        self.users = FakeCollection("users")
        self.chat_sessions = FakeCollection("chat_sessions")
        self.chat_messages = FakeCollection("chat_messages")
        self.interview_notes = FakeCollection("interview_notes")
        self.email_config = FakeCollection("email_config")
        self.email_templates = FakeCollection("email_templates")


class FakeRedis:
    """模拟 Redis 异步客户端"""

    def __init__(self):
        self._store: dict[str, str] = {}

    async def get(self, key):
        return self._store.get(key)

    async def setex(self, key, ttl, value):
        self._store[key] = value

    async def exists(self, key):
        return 1 if key in self._store else 0

    async def delete(self, *keys):
        deleted = 0
        for k in keys:
            if k in self._store:
                del self._store[k]
                deleted += 1
        return deleted
