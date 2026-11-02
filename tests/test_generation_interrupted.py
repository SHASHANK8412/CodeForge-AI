from backend.generation.store import GenerationStore


def test_runs_cut_off_by_a_restart_are_closed_but_paused_runs_are_kept(tmp_path):
    store = GenerationStore(store_path=tmp_path / "generations.json")
    running = store.create("p", "u", "build a todo app")
    store.update_status(running, "running")
    paused = store.create("p", "u", "build a blog")
    store.update_status(paused, "waiting_for_approval")

    assert store.mark_interrupted() == 1
    assert store.get(running)["status"] == "failed"
    assert "Interrupted" in store.get(running)["error"]
    assert store.get(paused)["status"] == "waiting_for_approval"
