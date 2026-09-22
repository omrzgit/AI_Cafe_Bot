from langgraph.graph import StateGraph, START, END

from app.services.ai.graph_state import GraphState
from app.services.ai.nodes import llm_invoke, validate_output, finalize, route_state

def build_graph() -> StateGraph:
    """Construct and compile the booking state graph."""
    graph = StateGraph(GraphState)

    graph.add_node("llm_invoke", llm_invoke)
    graph.add_node("validate_output", validate_output)
    graph.add_node("finalize", finalize)

    graph.add_edge(START, "llm_invoke")
    graph.add_edge("llm_invoke", "validate_output")

    graph.add_conditional_edges("validate_output", route_state, {"finalize": "finalize"})
    graph.add_edge("finalize", END)

    return graph.compile()

booking_graph = build_graph()
