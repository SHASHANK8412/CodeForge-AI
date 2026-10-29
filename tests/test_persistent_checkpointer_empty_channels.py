from langgraph.checkpoint.base import empty_checkpoint

from backend.graph.persistent_checkpointer import PersistentCheckpointSaver


def test_checkpoint_with_empty_channel_round_trips(tmp_path):
    saver = PersistentCheckpointSaver(storage_dir=tmp_path)
    config = {"configurable": {"thread_id": "t1", "checkpoint_ns": ""}}

    checkpoint = empty_checkpoint()
    checkpoint["channel_values"] = {"plan": "build a todo app"}
    # "architecture" has a version but no value yet -> stored as the ("empty", b"") marker.
    checkpoint["channel_versions"] = {"plan": "1", "architecture": "1"}

    saved_config = saver.put(config, checkpoint, {"source": "loop", "step": 1}, checkpoint["channel_versions"])
    loaded = saver.get_tuple(saved_config)

    assert loaded is not None
    assert loaded.checkpoint["channel_values"] == {"plan": "build a todo app"}
