# nodes/config_selection.py

from typing import Dict, List
from langchain_core.language_models.chat_models import BaseChatModel

from agents.causal_analysis.state import Strategy
from utils.llm import call_llm

from ORCA.prompts.causal_analysis_prompts import (
    causal_strategy_prompt,
    strategy_output_parser
)

def clean_var_names(vars: List[str]) -> List[str]:
    return [v.split(".")[-1] if isinstance(v, str) and "." in v else v for v in vars]

def build_config_selection_node(llm: BaseChatModel):
    """
    Selects a causal strategy (task, identification method, estimator, refuter) 
    using an LLM based on user question, variables, and data sample.
    """

    def node(state: Dict) -> Dict:
        df_raw = state["df_raw"]
        parsed_vars = state["parsed_query"]
        question = state["input"]

        df_sample = df_raw.head(10).to_csv(index=False) if df_raw is not None else ""

        # Extract variables
        treatment = clean_var_names([parsed_vars.get("treatment")])[0]
        outcome = clean_var_names([parsed_vars.get("outcome")])[0]
        confounders = clean_var_names(parsed_vars.get("confounders", []))
        mediators = clean_var_names(parsed_vars.get("mediators", []))
        ivs = clean_var_names(parsed_vars.get("instrumental_variables", []))

        # Data type information
        unique_outcome_values = df_raw[outcome].dropna().unique()
        outcome_type = "binary" if len(unique_outcome_values) == 2 else "continuous"

        treatment_type = str(df_raw[treatment].dtype)

        prompt_input = {
            "question": question,
            "treatment": treatment,
            "outcome": outcome,
            "confounders": confounders,
            "mediators": mediators,
            "instrumental_variables": ivs,
            "df_sample": df_sample,
            "treatment_type": treatment_type,
            "outcome_type": outcome_type
        }

        result = call_llm(
            prompt=causal_strategy_prompt,
            parser=strategy_output_parser,
            variables=prompt_input,
            llm=llm
        )

        state["strategy"] = Strategy(
            task=result.causal_task,
            identification_method=result.identification_strategy,
            estimator=result.estimation_method,
            refuter=result.refutation_methods[0] if result.refutation_methods else None
        )
        return state

    return node