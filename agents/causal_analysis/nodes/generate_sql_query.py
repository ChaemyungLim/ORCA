# causal_analysis/nodes/generate_sql_query_node.py
import json, re
from typing import Dict
from prompts.causal_analysis_prompts import sql_generation_prompt 
from utils.llm import call_llm
from langchain_core.language_models.chat_models import BaseChatModel
from utils.redis_client import redis_client
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
def generate_valid_sql(llm, graph_nodes, expression_dict, schema_str):
    response = call_llm(
        prompt=sql_generation_prompt,
        # parser=sql_query_parser,
        variables={
            "selected_variables": graph_nodes,
            "variable_expressions": [expression_dict[var] for var in graph_nodes],
            "table_schemas": schema_str
        },
        llm=llm,
    )
    print('SQL Generation Response:', response)
    
    # Extract SQL query from the response
    sql_match = re.search(r"```sql\s*(.*?)```", response, re.DOTALL | re.IGNORECASE)
    if sql_match:
        sql_query = sql_match.group(1).strip()
    else:
        sql_query = response.strip()
    return sql_query

def build_generate_sql_query_node(llm: BaseChatModel):
    def node(state: Dict) -> Dict:
        graph_info = state["variable_info"]
        graph_nodes = state["causal_graph"]["nodes"]
        if not graph_info:
            raise ValueError("Missing parsed_info in state")
        
        schema_str = state["table_schema_str"]
        sql_query = generate_valid_sql(
            llm=llm,
            graph_nodes=graph_nodes,
            expression_dict=state["expression_dict"],
            schema_str=schema_str
        )
        
        state["sql_query"] = sql_query
        return state
    return node