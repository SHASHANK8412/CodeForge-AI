import logging

_logger = logging.getLogger("aiforge.performance")

class HuggingFaceGenerator:
    """
    Generates configuration settings for HuggingFace Space hosting,
    supporting Docker, Streamlit, and Gradio SDK specifications.
    """

    def __init__(self) -> None:
        pass

    def generate_config(self, app_name: str, sdk: str = "docker", port: int = 8000) -> str:
        """
        Creates huggingface.yml metadata configurations.
        """
        _logger.info(f"Generating HuggingFace config for: {app_name} with SDK: {sdk}")

        return f"""# HuggingFace Space Deployment Settings
title: {app_name}
emoji: 🚀
colorFrom: indigo
colorTo: purple
sdk: {sdk}
app_port: {port}
pinned: false
license: mit
"""
