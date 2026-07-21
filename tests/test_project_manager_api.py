from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_project_manager_endpoints():
    # 1. State endpoint
    res = client.get("/project/state")
    assert res.status_code == 200
    assert "project_name" in res.json()

    # 2. Update task state
    res_task = client.post("/project/task", json={
        "task_name": "database",
        "status": "Completed",
        "details": "Provisioned sqlite tables"
    })
    assert res_task.status_code == 200
    
    # 3. Sprints endpoint
    res_sprints = client.get("/project/sprints")
    assert res_sprints.status_code == 200
    assert len(res_sprints.json()) > 0

    # 4. Milestones endpoint
    res_milestones = client.get("/project/milestones")
    assert res_milestones.status_code == 200
    assert len(res_milestones.json()) > 0

    # 5. Daily standup endpoint
    res_standup = client.get("/project/standup")
    assert res_standup.status_code == 200
    assert "standup" in res_standup.json()

    # 6. Bug backlog endpoint
    res_bugs = client.get("/project/bugs")
    assert res_bugs.status_code == 200
    assert len(res_bugs.json()) > 0

    # 7. Decision memory ADRs
    res_decisions = client.get("/project/decisions")
    assert res_decisions.status_code == 200
    assert len(res_decisions.json()) > 0
