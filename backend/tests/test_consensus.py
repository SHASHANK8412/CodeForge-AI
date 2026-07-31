"""
Unit tests for Day 43 ConsensusEngine
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.services.consensus_engine import ConsensusEngine


class TestConsensusEngine(unittest.TestCase):

    def setUp(self):
        self.engine = ConsensusEngine()

    def test_candidate_evaluation_and_voting(self):
        candidates = [
            {
                "model": "qwen2.5-coder",
                "output": "import React from 'react'; export default function App() { return <div>UI</div>; }",
                "status": "SUCCESS",
                "latency": 2.1,
                "tokens_used": 150
            },
            {
                "model": "deepseek-coder",
                "output": "const App = () => <div>UI</div>;",
                "status": "SUCCESS",
                "latency": 2.5,
                "tokens_used": 120
            }
        ]

        result = self.engine.evaluate_candidates(candidates, task_type="React UI")
        self.assertGreaterEqual(result["consensus_pct"], 80.0)
        self.assertIn("winner_model", result)
        self.assertIn("voting_scores", result)
        self.assertEqual(len(result["evaluations"]), 2)


if __name__ == "__main__":
    unittest.main()
