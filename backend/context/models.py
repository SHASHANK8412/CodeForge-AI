"""
AIForge Conversation Intelligence Models
=======================================
Strongly-typed schemas for Conversation Messages, Conversation State,
Follow-Up Detection, Reference Resolution, and Context Results.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    """
    Typed message structure representing a single turn in a conversation.
    """
    id: str = Field(description="Unique message identifier")
    role: str = Field(description="Role: 'user', 'assistant', 'system'")
    content: str = Field(description="Message content text")
    timestamp: str = Field(default="", description="Timestamp string")
    intent: Optional[str] = Field(default=None, description="Classified intent for this turn")
    agent: Optional[str] = Field(default=None, description="Agent handling this turn")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Turn metadata")


class ConversationState(BaseModel):
    """
    Structured state representation of an active conversation session.
    """
    conversation_id: str
    messages: List[ConversationMessage] = Field(default_factory=list)
    current_topic: str = Field(default="")
    recent_intents: List[str] = Field(default_factory=list)
    active_agent: str = Field(default="ExplanationAgent")
    active_project_id: Optional[str] = Field(default=None)
    active_document: Optional[str] = Field(default=None)
    project_state: Dict[str, Any] = Field(default_factory=dict)
    summary: str = Field(default="")
    estimated_tokens: int = Field(default=0)


class ContextResult(BaseModel):
    """
    Result returned by ConversationContextManager for LLM generation context assembly.
    """
    conversation_id: str
    is_follow_up: bool = Field(default=False)
    follow_up_confidence: float = Field(default=0.0)
    topic: str = Field(default="")
    topic_shift: bool = Field(default=False)
    resolved_references: Dict[str, str] = Field(default_factory=dict)
    resolved_prompt: str = Field(description="Prompt text with resolved references for intent classifier")
    formatted_context: str = Field(default="", description="Formatted context snippet for specialized agents")
    selected_messages: List[ConversationMessage] = Field(default_factory=list)
    summary: str = Field(default="")
    active_project_id: Optional[str] = Field(default=None)
    active_document: Optional[str] = Field(default=None)
    estimated_tokens: int = Field(default=0)
