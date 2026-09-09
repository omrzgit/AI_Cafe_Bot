"""
LangGraph typed state for the appointment booking conversation graph.

GraphState is the single dictionary that flows through every node.
"""

from typing import Annotated, Optional
from typing_extensions import TypedDict
import operator

class GraphState(TypedDict):
    session_id: str
    user_message: str
    messages: Annotated[list[dict], operator.add]

    current_state: str
    next_state: str

    reply: str
    extracted: dict
    collected_data: dict

    services: list[dict]
    company_name: str

    show_services: bool
    error: Optional[str]
