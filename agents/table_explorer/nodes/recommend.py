from utils.llm import call_llm
from prompts.table_explorer_prompts import usecase_parser as parser, usecase_prompt as prompt
from langchain_core.language_models.chat_models import BaseChatModel

def get_related_graph(graph: dict, table_name: str) -> dict:
    related = {}
    # outbound
    for to_table in graph["edges"].get(table_name, []):
        key = f"{table_name}→{to_table}"
        edge_data = graph.get("edge_reasons", {}).get(key, [])
        reasons = [d.get("reason", "No reason found") for d in edge_data]
        related[to_table] = "\n".join(reasons) if reasons else "No reason found"
    # inbound
    for from_table, to_tables in graph["edges"].items():
        if table_name in to_tables:
            key = f"{from_table}→{table_name}"
            edge_data = graph.get("edge_reasons", {}).get(key, [])
            reasons = [d.get("reason", "No reason found") for d in edge_data]
            related[from_table] = "\n".join(reasons) if reasons else "No reason found"
    return related

def related_tables(db_id: str, table_name: str) -> str:
    # update_table_relations(db_id)
    graph_raw= redis_client.get(f"{db_id}:table_relations")
    graph = json.loads(graph_raw)
    related = get_related_graph(graph, table_name)
    return related

def recommend_analysis(table_name: str, db_id: str, table_description: str, llm: BaseChatModel) -> str:
    table_name = table_name
    db_id = db_id
    related = related_tables(db_id, table_name)

    recommendation = call_llm(
        prompt=prompt,
        parser=parser,
        variables={
            "table_description": table_description,
            "related_tables": related
        },
        llm=llm
    )
    return recommendation

def recommend_analysis_node(state, llm):
    table_name = state["input"]
    db_id = state["db_id"]    
    full_description = state["table_analysis"]
    related_tables_info = state["related_tables"]

    columns_info = full_description.get("columns", [])
    table_description = full_description.get("table_description", "")

    recommendation = recommend_analysis(table_name, db_id, table_description, llm)

    final_output = {
        "table_name": state.get("input", ""),
        "table_analysis": {
            "table_description": table_description.strip(),
            "columns": [
                {
                    "column_name": col["column_name"],
                    "data_type": col["data_type"],
                    "nullable": col["nullable"],
                    "nulls": col["nulls"],
                    "notes": col.get("notes", [])
                }
                for col in columns_info
            ],
            "analysis_considerations": full_description.get("analysis_considerations", "")
        },
        "related_tables": {
            table: reason for table, reason in related_tables_info.items()
        },
        "recommended_analysis": [
            {
                "Analysis_Topic": uc.analysis_topic,
                "Suggested_Methodology": uc.suggested_methodology,
                "Expected_Insights": uc.expected_insights
            }
            for uc in recommendation.usecases
        ]
    }

    return {
        "recommended_analysis": recommendation,
        "final_output": final_output
    }