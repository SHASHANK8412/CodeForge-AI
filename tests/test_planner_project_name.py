from backend.agents.planner_agent import DEFAULT_PROJECT_NAME, project_name_from_prompt


def test_unnamed_plans_get_a_name_from_the_prompt():
    assert project_name_from_prompt("Build a simple todo app with FastAPI and React") == "Todo App Fastapi React"
    assert project_name_from_prompt("Create an inventory tracker") == "Inventory Tracker"


def test_different_prompts_do_not_share_an_output_folder():
    assert project_name_from_prompt("todo list") != project_name_from_prompt("blog engine")


def test_empty_prompt_falls_back_to_the_default():
    assert project_name_from_prompt("") == DEFAULT_PROJECT_NAME
