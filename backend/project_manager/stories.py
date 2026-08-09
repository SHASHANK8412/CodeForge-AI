import logging
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.project_manager.stories")


class UserStoryGenerator:
    """
    UserStoryGenerator converts Epics into Agile User Stories ("As a user, I want...").
    """

    def generate_stories(self, epics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        stories = []
        story_id_counter = 1

        for epic in epics:
            e_id = epic["id"]
            if e_id == "EP-01":
                stories.append({
                    "id": f"US-{story_id_counter:02d}",
                    "epic_id": e_id,
                    "title": "User Account Registration",
                    "user_story": "As a user, I want to register an account so that I can access the system.",
                    "points": 3
                })
                story_id_counter += 1
                stories.append({
                    "id": f"US-{story_id_counter:02d}",
                    "epic_id": e_id,
                    "title": "JWT Token Login",
                    "user_story": "As a user, I want to log in using my credentials to receive a JWT access token.",
                    "points": 3
                })
                story_id_counter += 1
            else:
                stories.append({
                    "id": f"US-{story_id_counter:02d}",
                    "epic_id": e_id,
                    "title": f"Feature Story for {epic['title']}",
                    "user_story": f"As a user, I want to interact with {epic['title']} functionality.",
                    "points": 5
                })
                story_id_counter += 1

        logger.info(f"UserStoryGenerator generated {len(stories)} stories.")
        return stories


# Global UserStoryGenerator Instance
global_user_story_generator = UserStoryGenerator()
