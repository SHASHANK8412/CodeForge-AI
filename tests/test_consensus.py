import pytest
from backend.debate.consensus import ConsensusEngine
from backend.debate.voting import DebateVoting

def test_conflict_detection():
    engine = ConsensusEngine()
    
    # 1. SQL vs NoSQL Conflict
    p1 = {"database": "SQL", "architect": "NoSQL"}
    c1 = engine.detect_conflicts(p1)
    assert len(c1) == 1
    assert "SQL" in c1[0] and "NoSQL" in c1[0]

    # 2. REST vs GraphQL Conflict
    p2 = {"backend": "REST", "frontend": "GraphQL"}
    c2 = engine.detect_conflicts(p2)
    assert len(c2) == 1
    assert "REST" in c2[0] and "GraphQL" in c2[0]

    # 3. Safe/Concordant Proposals
    p3 = {"backend": "REST", "frontend": "REST"}
    c3 = engine.detect_conflicts(p3)
    assert len(c3) == 0

def test_weighted_voting():
    voting = DebateVoting()
    
    # Votes layout: backend prefers REST, database prefers SQL, architect prefers GraphQL
    votes = {
        "backend": "REST",
        "database": "SQL",
        "architect": "GraphQL"
    }
    # Confidences mapping
    confidences = {
        "backend": 100.0,
        "database": 90.0,
        "architect": 80.0
    }
    
    tallies = voting.calculate_weighted_votes(votes, confidences)
    
    # Architect weight is 5.0 * 80% = 4.0
    # Backend weight is 4.0 * 100% = 4.0
    # Database weight is 4.0 * 90% = 3.6
    assert tallies["GraphQL"] == 4.0
    assert tallies["REST"] == 4.0
    assert tallies["SQL"] == 3.6

def test_winning_solution_resolution():
    engine = ConsensusEngine()
    
    # 1. Tally check
    tallies = {"REST": 8.0, "GraphQL": 4.0}
    decision = engine.calculate_winning_solution(tallies, [])
    assert decision["solution"] == "REST"
    assert "highest weighted" in decision["reason"]

    # 2. Conflict resolution check
    conflicts = ["REST vs GraphQL"]
    decision_conf = engine.calculate_winning_solution(tallies, conflicts)
    assert "Resolved design conflicts" in decision_conf["reason"]
