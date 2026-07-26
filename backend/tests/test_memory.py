import pytest
from backend.memory.memory_manager import MemoryManager


@pytest.fixture
def memory():
    """Provides a fresh MemoryManager instance for each unit test."""
    return MemoryManager()


def test_save_memory(memory):
    """Test 1: Store output for an agent and verify saving."""
    session_id = "session_test_1"
    planner_data = {
        "project_name": "AI Chat App",
        "features": ["Auth", "Chat UI", "RAG"]
    }
    memory.save_agent_output(session_id, "planner", planner_data)

    stored = memory.get_agent_output(session_id, "planner")
    assert stored["project_name"] == "AI Chat App"
    assert "Auth" in stored["features"]


def test_read_memory(memory):
    """Test 2: Retrieve previous outputs across multiple agents."""
    session_id = "session_test_2"
    memory.save_agent_output(session_id, "architect", {"style": "Microservices", "layers": 3})
    memory.save_agent_output(session_id, "backend", {"framework": "FastAPI", "version": "0.100"})

    arch_out = memory.get_agent_output(session_id, "architect")
    be_out = memory.get_agent_output(session_id, "backend")

    assert arch_out["style"] == "Microservices"
    assert be_out["framework"] == "FastAPI"


def test_update_memory(memory):
    """Test 3: Update and merge agent memory outputs."""
    session_id = "session_test_3"
    memory.save_agent_output(session_id, "frontend", {"framework": "React", "components": ["Header"]})

    # Update frontend memory with new components
    memory.update_agent_output(session_id, "frontend", {"components": ["Header", "Footer", "ChatBox"]})

    updated = memory.get_agent_output(session_id, "frontend")
    assert updated["framework"] == "React"
    assert len(updated["components"]) == 3
    assert "Footer" in updated["components"]


def test_delete_memory(memory):
    """Test 4: Delete specific agent output and clear session."""
    session_id = "session_test_4"
    memory.save_agent_output(session_id, "database", {"db_type": "PostgreSQL"})

    # Verify existing
    assert memory.get_agent_output(session_id, "database")["db_type"] == "PostgreSQL"

    # Delete database memory
    deleted = memory.delete_agent_output(session_id, "database")
    assert deleted is True
    assert memory.get_agent_output(session_id, "database") == {}


def test_multiple_sessions(memory):
    """Test 5: Maintain multiple simultaneous project sessions without context bleeding."""
    # Session 1: AI Chat App
    s1 = memory.create_session("session_1", "AI Chat App")
    memory.save_agent_output("session_1", "planner", {"app_type": "Chat"})

    # Session 2: E-commerce
    s2 = memory.create_session("session_2", "E-commerce Platform")
    memory.save_agent_output("session_2", "planner", {"app_type": "Store"})

    # Session 3: Hospital Management
    s3 = memory.create_session("session_3", "Hospital System")
    memory.save_agent_output("session_3", "planner", {"app_type": "Healthcare"})

    assert memory.get_session("session_1").project_name == "AI Chat App"
    assert memory.get_session("session_2").project_name == "E-commerce Platform"
    assert memory.get_session("session_3").project_name == "Hospital System"

    active_sessions = memory.session_manager.list_sessions()
    assert len(active_sessions) == 3


def test_context_sharing_and_agent_sync(memory):
    """Test 6: Context sharing between agents & duplicate generation prevention."""
    session_id = "session_sync"
    memory.create_session(session_id, "Shared App")

    # Step 1: Planner output
    memory.save_agent_output(session_id, "planner", {
        "project_name": "Shared App",
        "tech_stack": {
            "authentication": "JWT",
            "frontend": "React",
            "backend": "FastAPI",
            "database": "PostgreSQL"
        }
    })

    # Verify shared stack extraction
    shared_stack = memory.context_store.extract_shared_stack()
    assert shared_stack["authentication"] == "JWT"
    assert shared_stack["frontend"] == "React"

    # Step 2: Register generated files to prevent duplicate generation
    memory.save_agent_output(session_id, "frontend", {
        "frontend/src/components/Login.jsx": "export default function Login() {}"
    })

    assert memory.is_file_generated(session_id, "frontend/src/components/Login.jsx") is True
    existing = memory.get_existing_files(session_id)
    assert "frontend/src/components/Login.jsx" in existing

    # Step 3: Complete project memory snapshot
    full_memory = memory.get_project_memory(session_id)
    assert full_memory["session_id"] == session_id
    assert "planner" in full_memory["context"]
    assert "frontend/src/components/Login.jsx" in full_memory["generated_files"]
