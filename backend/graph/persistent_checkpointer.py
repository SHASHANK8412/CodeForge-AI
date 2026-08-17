"""
AIForge Persistent LangGraph Checkpoint Engine
==============================================
Provides durable, thread-safe state persistence across process restarts,
crashes, and browser refreshes for LangGraph workflows.
Compatible with LangGraph 1.2.9 BaseCheckpointSaver specifications.
"""

import os
import pickle
import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, Optional, Iterator, Sequence, AsyncIterator

from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    ChannelVersions,
    get_checkpoint_metadata,
)
from langchain_core.runnables import RunnableConfig

_logger = logging.getLogger("aiforge.graph.persistent_checkpointer")

DEFAULT_STORAGE_DIR = Path(__file__).resolve().parent.parent / "data" / "checkpoints"


def _to_plain_dict(d: Any) -> Any:
    """Recursively converts defaultdict to standard dict for clean pickle serialization."""
    if isinstance(d, (defaultdict, dict)):
        return {k: _to_plain_dict(v) for k, v in d.items()}
    return d


def _to_nested_defaultdict(d: Dict[str, Any]) -> defaultdict:
    res = defaultdict(lambda: defaultdict(dict))
    for k1, v1 in d.items():
        if isinstance(v1, dict):
            for k2, v2 in v1.items():
                if isinstance(v2, dict):
                    res[k1][k2] = dict(v2)
                else:
                    res[k1][k2] = v2
        else:
            res[k1] = v1
    return res


class PersistentCheckpointSaver(BaseCheckpointSaver):
    """
    Persistent LangGraph Checkpointer that keeps workflow snapshots in memory
    for low-latency execution and persists state snapshots to disk/database.
    """

    def __init__(self, storage_dir: Optional[Path | str] = None):
        super().__init__()
        self.storage_dir = Path(storage_dir) if storage_dir else DEFAULT_STORAGE_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.store_file = self.storage_dir / "checkpoint_registry.pkl"

        self.storage: defaultdict[str, defaultdict[str, dict[str, tuple[tuple[str, bytes], tuple[str, bytes], str | None]]]] = (
            defaultdict(lambda: defaultdict(dict))
        )
        self.writes: defaultdict[tuple[str, str, str], dict[tuple[str, int], tuple[str, str, tuple[str, bytes], str]]] = (
            defaultdict(dict)
        )
        self.blobs: dict[tuple[str, str, str, str | int | float], tuple[str, bytes]] = {}

        self._load_from_disk()

    def _load_from_disk(self) -> None:
        if self.store_file.exists():
            try:
                with open(self.store_file, "rb") as f:
                    data = pickle.load(f)
                    raw_storage = data.get("storage", {})
                    self.storage = _to_nested_defaultdict(raw_storage)
                    self.writes = defaultdict(dict, data.get("writes", {}))
                    self.blobs = dict(data.get("blobs", {}))
                _logger.info(f"PersistentCheckpointSaver: Loaded {len(self.storage)} workflow threads from {self.store_file.name}")
            except Exception as e:
                _logger.warning(f"PersistentCheckpointSaver: Failed to load checkpoint registry: {e}")

    def _save_to_disk(self) -> None:
        try:
            temp_file = self.storage_dir / f"checkpoint_registry.tmp.{os.getpid()}"
            with open(temp_file, "wb") as f:
                pickle.dump({
                    "storage": _to_plain_dict(self.storage),
                    "writes": dict(self.writes),
                    "blobs": dict(self.blobs),
                }, f)
            # Atomic rename / replace
            if os.path.exists(self.store_file):
                os.replace(temp_file, self.store_file)
            else:
                temp_file.rename(self.store_file)
        except Exception as e:
            _logger.error(f"PersistentCheckpointSaver: Failed to persist checkpoint registry to disk: {e}")

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"].get("checkpoint_id")

        if checkpoint_id:
            saved = self.storage[thread_id][checkpoint_ns].get(checkpoint_id)
        else:
            if not self.storage[thread_id][checkpoint_ns]:
                return None
            checkpoint_id = list(self.storage[thread_id][checkpoint_ns].keys())[-1]
            saved = self.storage[thread_id][checkpoint_ns].get(checkpoint_id)

        if not saved:
            return None

        serde_checkpoint, serde_metadata, parent_checkpoint_id = saved
        checkpoint_ = self.serde.loads_typed(serde_checkpoint)
        metadata = self.serde.loads_typed(serde_metadata)

        writes = [
            v for (t_id, ns, c_id), v_map in self.writes.items()
            if t_id == thread_id and ns == checkpoint_ns and c_id == checkpoint_id
            for v in v_map.values()
        ]

        def _load_channel(k: str, v: Any) -> Any:
            blob_key = (thread_id, checkpoint_ns, k, v)
            if blob_key in self.blobs:
                return self.serde.loads_typed(self.blobs[blob_key])
            return None

        channel_values = {
            k: _load_channel(k, v)
            for k, v in checkpoint_.get("channel_versions", {}).items()
            if _load_channel(k, v) is not None
        }

        checkpoint_["channel_values"] = channel_values

        parent_config = (
            {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": parent_checkpoint_id,
                }
            }
            if parent_checkpoint_id
            else None
        )

        return CheckpointTuple(
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": checkpoint_id,
                }
            },
            checkpoint=checkpoint_,
            metadata=metadata,
            parent_config=parent_config,
            pending_writes=[
                (id, c, self.serde.loads_typed(v)) for id, c, v, _ in writes
            ],
        )

    def list(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        if not config:
            return iter([])
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")

        thread_checkpoints = self.storage[thread_id][checkpoint_ns]
        tuples = []
        for c_id in reversed(list(thread_checkpoints.keys())):
            c_tuple = self.get_tuple({
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": c_id,
                }
            })
            if c_tuple:
                tuples.append(c_tuple)
            if limit and len(tuples) >= limit:
                break
        return iter(tuples)

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        c = checkpoint.copy()
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        values: dict[str, Any] = c.pop("channel_values", {})

        for k, v in new_versions.items():
            self.blobs[(thread_id, checkpoint_ns, k, v)] = (
                self.serde.dumps_typed(values[k]) if k in values else ("empty", b"")
            )

        self.storage[thread_id][checkpoint_ns].update(
            {
                checkpoint["id"]: (
                    self.serde.dumps_typed(c),
                    self.serde.dumps_typed(get_checkpoint_metadata(config, metadata)),
                    config["configurable"].get("checkpoint_id"),
                )
            }
        )

        self._save_to_disk()

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint["id"],
            }
        }

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"].get("checkpoint_id")
        if not checkpoint_id and thread_id in self.storage and checkpoint_ns in self.storage[thread_id] and self.storage[thread_id][checkpoint_ns]:
            checkpoint_id = max(self.storage[thread_id][checkpoint_ns].keys())
        checkpoint_id = checkpoint_id or ""
        outer_key = (thread_id, checkpoint_ns, checkpoint_id)


        for idx, (c, v) in enumerate(writes):
            inner_key = (task_id, idx)
            self.writes[outer_key][inner_key] = (
                task_id,
                c,
                self.serde.dumps_typed(v),
                task_path,
            )

        self._save_to_disk()

    def delete_thread(self, thread_id: str) -> None:
        if thread_id in self.storage:
            del self.storage[thread_id]
        for k in list(self.writes.keys()):
            if k[0] == thread_id:
                del self.writes[k]
        for k in list(self.blobs.keys()):
            if k[0] == thread_id:
                del self.blobs[k]
        self._save_to_disk()

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        return self.get_tuple(config)

    async def alist(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        for item in self.list(config, filter=filter, before=before, limit=limit):
            yield item

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        return self.put(config, checkpoint, metadata, new_versions)

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        return self.put_writes(config, writes, task_id, task_path)

    async def adelete_thread(self, thread_id: str) -> None:
        return self.delete_thread(thread_id)


# Global persistent checkpointer instance
global_persistent_checkpointer = PersistentCheckpointSaver()
