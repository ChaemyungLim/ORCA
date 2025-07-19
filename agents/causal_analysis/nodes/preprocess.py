# causal_analysis/nodes/preprocess.py

import pandas as pd
from typing import Dict
from utils.assist_preprocessing import drop_nulls, normalize_covariates

def build_preprocess_node():
        
    def node(state: Dict) -> Dict:
        df: pd.DataFrame = state["df_raw"]
        graph_nodes = state["causal_graph"]["nodes"]
        parsed_query = state["parsed_query"]

        if df is None or not graph_nodes:
            raise ValueError("Missing 'df_raw' or 'causal_graph.nodes'.")

        selected_cols = [var.split(".")[-1] for var in graph_nodes]
        df = df[selected_cols].copy()

        for col in df.columns:
            if df[col].dtype == object:
                try:
                    df[col] = pd.to_numeric(df[col])
                except Exception:
                    df[col] = df[col].astype("category")
                    
        # 🔒 Optional Normalization
        # df = drop_nulls(df)

        # treatment = parsed_query.get("treatment")
        # outcome = parsed_query.get("outcome")
        # df = normalize_covariates(df, treatment, outcome)

        state["df_preprocessed"] = df
        return state

    return node