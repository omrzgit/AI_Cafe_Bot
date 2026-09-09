import json
import logging
from datetime import datetime
from typing import Any

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers.json import parse_json_markdown

from app.config.llm_client import get_llm
from app.services.ai.prompts import build_prompt
from app.services.ai.graph_state import GraphState

logger = logging.getLogger(__name__)

VALID_STATES = frozenset(
    {"GREET", "LIST_SERVICES", "SELECT_SERVICE", "COLLECT_DETAILS", "CONFIRM", "BOOKED"}
)

_FALLBACK = {
    "reply": "I'm having a little trouble processing that. Could you please repeat your request?",
    "next_state": "GREET",
    "extracted": {},
}

async def llm_invoke(state: GraphState) -> dict[str, Any]:
    llm = get_llm()

    prompt = build_prompt(
        current_state=state["current_state"],
        collected_data=state.get("collected_data", {}),
        services=state.get("services", []),
        company_name=state.get("company_name", ""),
    )

    history: list = []
    for msg in state.get("messages", []):
        if msg["role"] == "user":
            history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            history.append(AIMessage(content=msg["content"]))

    chain = prompt | llm

    try:
        ai_message = await chain.ainvoke({
            "history": history,
            "user_message": state["user_message"],
        })
        raw_text: str = ai_message.content

        try:
            parsed = parse_json_markdown(raw_text)
        except Exception:
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                inner = []
                for line in lines[1:]:
                    if line.strip() == "```":
                        break
                    inner.append(line)
                cleaned = "\n".join(inner)
            parsed = json.loads(cleaned)

    except Exception as e:
        logger.warning(f"LLM call / JSON parse failed: {e}")
        parsed = _FALLBACK.copy()

    reply = parsed.get("reply") or _FALLBACK["reply"]
    next_state = parsed.get("next_state") or state["current_state"]
    extracted = parsed.get("extracted") or {}

    return {
        "reply": reply,
        "next_state": next_state,
        "extracted": extracted,
        "messages": [
            {"role": "user", "content": state["user_message"]},
            {"role": "assistant", "content": reply},
        ],
    }

def validate_output(state: GraphState) -> dict[str, Any]:
    next_state = state.get("next_state", state["current_state"])
    if next_state not in VALID_STATES:
        logger.warning(f"Invalid next_state '{next_state}' ? keeping {state['current_state']}")
        next_state = state["current_state"]

    collected = dict(state.get("collected_data", {}))
    for key, value in (state.get("extracted") or {}).items():
        if value and key != "services_list":
            collected[key] = value

    if collected.get("date"):
        try:
            d = datetime.strptime(collected["date"], "%Y-%m-%d").date()
            if d < datetime.utcnow().date():
                logger.warning(f"Past date rejected: {collected['date']}")
                del collected["date"]
        except ValueError:
            logger.warning(f"Bad date format: {collected['date']}")
            del collected["date"]

    if collected.get("time"):
        try:
            parts = str(collected["time"]).split(":")
            h, m = int(parts[0]), int(parts[1])
            if 0 <= h <= 23 and 0 <= m <= 59:
                collected["time"] = f"{h:02d}:{m:02d}"
            else:
                del collected["time"]
        except (ValueError, IndexError, AttributeError):
            del collected["time"]

    if collected.get("email"):
        parts = str(collected["email"]).split("@")
        if len(parts) != 2 or "." not in parts[1]:
            del collected["email"]

    required = {"service", "name", "email", "date", "time"}
    if next_state == "COLLECT_DETAILS" and required.issubset(
        {k for k, v in collected.items() if v}
    ):
        next_state = "CONFIRM"

    return {
        "current_state": next_state,
        "collected_data": collected,
    }

def finalize(state: GraphState) -> dict[str, Any]:
    current_state = state["current_state"]
    extracted = state.get("extracted") or {}

    show_services = bool(extracted.get("services_list")) or current_state == "LIST_SERVICES"
    trimmed = state.get("messages", [])[-20:]

    return {
        "show_services": show_services,
        "messages": [],
        "_trimmed_messages": trimmed,
    }

def route_state(state: GraphState) -> str:
    return "finalize"
