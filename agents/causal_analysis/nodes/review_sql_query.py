# causal_analysis/nodes/generate_sql_query_node.py
import json, re
from typing import Dict
from prompts.causal_analysis_prompts import sql_review_prompt 
from utils.llm import call_llm
from langchain_core.language_models.chat_models import BaseChatModel
from utils.redis_client import redis_client

def review_sql(llm, graph_nodes, expression_dict, schema_str, sql_query):
    response = call_llm(
        prompt=sql_review_prompt,
        # parser=sql_query_parser,
        variables={
            "selected_variables": graph_nodes,
            "variable_expressions": [expression_dict[var] for var in graph_nodes],
            "table_schemas": schema_str,
            "sql": sql_query
        },
        llm=llm,
    )

    sql_match = re.search(r"```sql\s*(.*?)```", response, re.DOTALL | re.IGNORECASE)
    if sql_match:
        revised_query = sql_match.group(1).strip()
    else:
        revised_query = None
    return revised_query

def build_review_sql_query_node(llm: BaseChatModel):
    def node(state: Dict) -> Dict:
        graph_info = state["variable_info"]
        graph_nodes = state["causal_graph"]["nodes"]
        if not graph_info:
            raise ValueError("Missing parsed_info in state")
        
        schema_str = state["table_schema_str"]
        sql_query = review_sql(
            llm=llm,
            graph_nodes=graph_nodes,
            expression_dict=state["expression_dict"],
            schema_str=schema_str,
            sql_query=state["sql_query"]
        )
        
        if sql_query:
            state["sql_query"] = sql_query
        return state
    return node