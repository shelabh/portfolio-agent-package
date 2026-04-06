from __future__ import annotations
import pickle
import msgpack
import time
from typing import Any, Dict, Optional, Tuple
import logging

import redis

logger = logging.getLogger(__name__)

def _pack_payload(obj: Any) -> bytes:
    try:
        packed = msgpack.packb(obj, use_bin_type=True)
        return b"MP" + packed
    except Exception:
        return b"PK" + pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)

def _unpack_payload(data: bytes) -> Any:
    if data[:2] == b"MP":
        return msgpack.unpackb(data[2:], raw=False)
    elif data[:2] == b"PK":
        return pickle.loads(data[2:])
    else:
        return pickle.loads(data)

class RedisCheckpointer:
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        prefix: str = "portfolio_agent",
        ttl_seconds: Optional[int] = None,
        redis_kwargs: Optional[Dict[str, Any]] = None,
    ):
        self.prefix = prefix.rstrip(":")
        self.ttl = ttl_seconds
        self._client = redis.Redis.from_url(redis_url, **(redis_kwargs or {}))
        try:
            self._client.ping()
        except Exception as exc:
            logger.exception("Failed to connect to Redis at %s", redis_url)
            raise

    def _cp_key(self, thread_id: str, checkpoint_id: str) -> str:
        return f"{self.prefix}:checkpoint:{thread_id}:{checkpoint_id}"

    def _checkpoints_set_key(self, thread_id: str) -> str:
        return f"{self.prefix}:checkpoints:{thread_id}"

    def _writes_key(self, thread_id: str, write_id: str) -> str:
        return f"{self.prefix}:writes:{thread_id}:{write_id}"

    def put(self, thread_id: str, checkpoint_id: str, payload: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        key = self._cp_key(thread_id, checkpoint_id)
        packed = _pack_payload({"payload": payload, "metadata": metadata or {}, "ts": time.time()})
        pipeline = self._client.pipeline()
        pipeline.set(key, packed)
        if self.ttl:
            pipeline.expire(key, self.ttl)
        pipeline.zadd(self._checkpoints_set_key(thread_id), {checkpoint_id: time.time()})
        pipeline.execute()

    def put_writes(self, thread_id: str, write_id: str, payload: Any) -> None:
        key = self._writes_key(thread_id, write_id)
        packed = _pack_payload({"payload": payload, "ts": time.time()})
        pipeline = self._client.pipeline()
        pipeline.set(key, packed)
        if self.ttl:
            pipeline.expire(key, self.ttl)
        pipeline.execute()

    def get_tuple(self, thread_id: str, checkpoint_id: str) -> Optional[Tuple[Any, Dict[str, Any]]]:
        key = self._cp_key(thread_id, checkpoint_id)
        raw = self._client.get(key)
        if raw is None:
            return None
        try:
            decoded = _unpack_payload(raw)
            return decoded.get("payload"), decoded.get("metadata", {})
        except Exception:
            logger.exception("Failed to decode checkpoint payload for key %s", key)
            return None

    def list_checkpoints(self, thread_id: str, start=0, end=-1):
        key = self._checkpoints_set_key(thread_id)
        return [x.decode() if isinstance(x, bytes) else x for x in self._client.zrange(key, start, end)]

    def latest_checkpoint(self, thread_id: str) -> Optional[Tuple[str, Any]]:
        key = self._checkpoints_set_key(thread_id)
        res = self._client.zrevrange(key, 0, 0)
        if not res:
            return None
        cp_id = res[0].decode() if isinstance(res[0], bytes) else res[0]
        payload_meta = self.get_tuple(thread_id, cp_id)
        return (cp_id, payload_meta[0]) if payload_meta else None
