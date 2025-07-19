# agents/causal_analysis/graph.py
from langgraph.graph import StateGraph, END

from .state import CausalAnalysisState
from .nodes.parse_question import build_parse_question_node
from .nodes.generate_sql_query import build_generate_sql_query_node
from .nodes.review_sql_query import build_review_sql_query_node
from .nodes.fetch_data import build_fetch_data_node
from .nodes.preprocess import build_preprocess_node
from .nodes.config_selection import build_config_selection_node
from .nodes.dowhy_analysis import build_dowhy_analysis_node
from .nodes.generate_answer import build_generate_answer_node

def generate_causal_analysis_graph(llm):
    graph = StateGraph(CausalAnalysisState)

    # Add entry node for conditional routing
    graph.add_node("__entry__", lambda state: state)
    
    # Add nodes
    graph.add_node("parse_question", build_parse_question_node(llm))
    graph.add_node("generate_sql_query", build_generate_sql_query_node(llm))
    graph.add_node("review_sql_query", build_review_sql_query_node(llm))
    graph.add_node("fetch_data", build_fetch_data_node(llm))
    graph.add_node("preprocess", build_preprocess_node())
    graph.add_node("config_selection", build_config_selection_node(llm))
    graph.add_node("dowhy_analysis", build_dowhy_analysis_node())
    graph.add_node("generate_answer", build_generate_answer_node(llm))

    # Conditional branching from parse_question
    def route_entry(state):
        if state["sql_query"]:
            return "fetch_data"
        else:
            return "generate_sql_query"

    graph.set_entry_point("__entry__")
    graph.add_conditional_edges("__entry__", route_entry)

    graph.add_edge("generate_sql_query", "review_sql_query")
    graph.add_edge("review_sql_query", "fetch_data")
    graph.add_edge("fetch_data", "preprocess")
    graph.add_edge("preprocess", "config_selection")
    graph.add_edge("config_selection", "dowhy_analysis")
    graph.add_edge("dowhy_analysis", "generate_answer")
    graph.add_edge("generate_answer", END)

    return graph.compile()