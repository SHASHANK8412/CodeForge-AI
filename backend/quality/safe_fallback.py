"""
AIForge Safe Fallback Provider
==============================
Provides safe, clean, user-facing fallback responses when automatic generation/regeneration fails.
Ensures malformed or bad LLM responses never reach the UI.
"""

from typing import List, Optional


def get_safe_fallback_response(intent: str, user_prompt: str, issues: Optional[List[str]] = None) -> str:
    """
    Returns a safe, friendly fallback response tailored to intent and failure reason.
    """
    issue_summary = f" ({'; '.join(issues[:2])})" if issues else ""

    if intent in ["EXPLANATION", "GENERAL_QA"]:
        return (
            f"### ℹ️ Response Guidance\n\n"
            f"I was unable to generate a clean explanation for **'{user_prompt}'** that met our quality standards{issue_summary}.\n\n"
            f"Please try asking your question with specific aspects you would like explained (e.g., *'Explain {user_prompt} for beginners'*)."
        )
    elif intent in ["CODING", "DSA_PROBLEM"]:
        return (
            f"### ⚠️ Code Generation Fallback\n\n"
            f"I could not generate a valid code implementation for **'{user_prompt}'** that passed contract validation{issue_summary}.\n\n"
            f"Please specify the desired programming language or input/output requirements clearly."
        )
    elif intent == "DEBUGGING":
        return (
            f"### 🐛 Debugging Fallback\n\n"
            f"I couldn't analyze the code error for **'{user_prompt}'** with high confidence{issue_summary}.\n\n"
            f"Please paste the exact code snippet along with the error traceback for an accurate diagnosis."
        )
    elif intent == "RESUME":
        return (
            f"### 📄 Resume Review Fallback\n\n"
            f"I couldn't complete the resume analysis for **'{user_prompt}'**{issue_summary}.\n\n"
            f"Please provide your resume bullet points or target job description."
        )
    elif intent == "RAG_QUERY":
        return (
            f"### 📚 Document Search Fallback\n\n"
            f"I could not find sufficient grounded context in the uploaded documents to answer **'{user_prompt}'** accurately.\n\n"
            f"Please ensure the document contains relevant information or rephrase your query."
        )
    else:
        return (
            f"### ⚠️ Unable to Complete Request\n\n"
            f"I couldn't generate a response that met quality requirements for **'{user_prompt}'**{issue_summary}.\n\n"
            f"Please try rephrasing your request or selecting a specific task type."
        )
