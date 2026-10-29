from backend.generation.manager import _approval_stage


def test_final_checkpoint_is_not_reported_as_architecture():
    # state still carries the value written at the first (architecture) checkpoint
    stale = {"approval_stage": "architecture"}
    assert _approval_stage(("final_approval",), stale) == "final"


def test_architecture_checkpoint():
    assert _approval_stage(("human_approval",), {}) == "architecture"


def test_falls_back_to_state_when_not_paused():
    assert _approval_stage((), {"approval_stage": "final"}) == "final"
