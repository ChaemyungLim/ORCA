# agents/causal_analysis/state.py

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict
import pandas as pd
from dowhy import CausalModel
from dowhy.causal_estimator import CausalEstimate

class Strategy(BaseModel):
    task: str
    identification_method: str
    estimator: str
    refuter: Optional[str] = None

class CausalAnalysisState(BaseModel):
    messages: Optional[List] = [] 
    model_config = ConfigDict(arbitrary_types_allowed=True)
        
    input: Optional[str] = None  
    db_id: Optional[str] = "daa" 
    
    parsed_query: Optional[Dict[str, Any]] = None 
    table_schema_str: Optional[str] = None
    
    sql_query: Optional[str] = None 
    df_raw: Optional[pd.DataFrame] = None  
    df_preprocessed: Optional[pd.DataFrame] = None 
    label_maps: Optional[Dict[str, Dict[int, str]]] = None  

    variable_info: Optional[Dict[str, Any]] = None  
    expression_dict: Optional[Dict[str, str]] = None 
    causal_graph: Optional[Dict[str, Any]] = None  
    
    strategy: Optional[Strategy] = None  
    causal_model: Optional[CausalModel] = None  # dowhy model
    causal_estimand: Optional[Any] = None  
    causal_estimate: Optional[CausalEstimate] = None  
    causal_effect_ate: Optional[float] = None  # ATE (Average Treatment Effect)
    causal_effect_ci: Optional[Any] = None 
    refutation_result: Optional[str] = None 
    final_answer: Optional[str] = None 
    
    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)