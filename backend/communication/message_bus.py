"""
AIForge Centralized Agent Message Bus
=====================================
Central communication bus managing agent message queues, inboxes, delivery routing, and interaction logging.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from backend.communication.protocol import AgentMessage, MessageType, MessagePriority
from backend.communication.communication_logger import global_communication_logger
from backend.communication.events import global_event_dispatcher, SystemEventType

_logger = logging.getLogger("aiforge.communication.bus")


class MessageBus:
    """
    Centralized Message Bus managing agent inboxes and routing.
    """

    def __init__(self) -> None:
        self.inboxes: Dict[str, List[Dict[str, Any]]] = {}
        self.all_messages: Dict[str, AgentMessage] = {}
        self._seed_default_messages()

    def _seed_default_messages(self) -> None:
        default_msgs = [
            AgentMessage(
                sender="Planner Agent",
                receiver="Architect Agent",
                type=MessageType.TASK,
                priority=MessagePriority.HIGH,
                payload={"summary": "Generate architecture for Food Delivery App.", "prompt": "Food Delivery App"}
            ),
            AgentMessage(
                sender="Architect Agent",
                receiver="Frontend Agent",
                type=MessageType.EVENT,
                priority=MessagePriority.MEDIUM,
                payload={"summary": "Authentication module completed. Start UI generation."}
            ),
            AgentMessage(
                sender="Backend Agent",
                receiver="Database Agent",
                type=MessageType.REQUEST,
                priority=MessagePriority.HIGH,
                payload={"summary": "Need schema for User & Patient tables."}
            ),
            AgentMessage(
                sender="Testing Agent",
                receiver="Backend Agent",
                type=MessageType.ERROR,
                priority=MessagePriority.HIGH,
                payload={"summary": "API /login failed with HTTP 500. Please investigate."}
            ),
            AgentMessage(
                sender="Reviewer Agent",
                receiver="Frontend Agent",
                type=MessageType.WARNING,
                priority=MessagePriority.MEDIUM,
                payload={"summary": "Improve accessibility: Increase button contrast & refactor component naming."}
            )
        ]
        for msg in default_msgs:
            self.send_message(msg)

    def send_message(self, message: AgentMessage) -> Dict[str, Any]:
        self.all_messages[message.id] = message
        
        # Deliver to receiver inbox
        receiver = message.receiver
        if receiver not in self.inboxes:
            self.inboxes[receiver] = []
        
        msg_dict = message.to_dict()
        self.inboxes[receiver].append(msg_dict)

        # Log interaction
        global_communication_logger.log_message(message)

        # Dispatch event
        global_event_dispatcher.publish(
            event_type=SystemEventType.TASK_ASSIGNED if message.type == MessageType.TASK else SystemEventType.TASK_COMPLETED,
            publisher=message.sender,
            data={"receiver": message.receiver, "summary": message.payload.get("summary", "")}
        )

        _logger.info(f"MessageBus: Routed message '{message.id}' from '{message.sender}' to '{message.receiver}'")
        return msg_dict

    def get_agent_inbox(self, agent_name: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        # Match case-insensitively or exact match
        inbox = []
        for k, msgs in self.inboxes.items():
            if k.lower() == agent_name.lower() or agent_name.lower() in k.lower():
                inbox.extend(msgs)

        if unread_only:
            inbox = [m for m in inbox if not m.get("processed", False)]
        return inbox

    def get_all_messages(self, agent: Optional[str] = None) -> List[Dict[str, Any]]:
        msgs = [m.to_dict() for m in self.all_messages.values()]
        if agent:
            a_lower = agent.lower()
            msgs = [
                m for m in msgs
                if a_lower in m["sender"].lower() or a_lower in m["receiver"].lower()
            ]
        return msgs

    def process_next_message(self, agent_name: str) -> Optional[Dict[str, Any]]:
        inbox = self.get_agent_inbox(agent_name, unread_only=True)
        if not inbox:
            return None

        # Process message with highest priority first
        prio_map = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        inbox.sort(key=lambda m: prio_map.get(m.get("priority", "MEDIUM"), 1), reverse=True)

        msg_dict = inbox[0]
        msg_id = msg_dict["id"]
        
        if msg_id in self.all_messages:
            self.all_messages[msg_id].processed = True
            self.all_messages[msg_id].acknowledged = True

        msg_dict["processed"] = True
        msg_dict["acknowledged"] = True
        _logger.info(f"MessageBus: Agent '{agent_name}' processed message '{msg_id}'")
        return msg_dict


global_message_bus = MessageBus()
