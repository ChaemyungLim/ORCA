from typing import List, Union
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate


# objective summary prompt and parser
class ObjectiveSummary(BaseModel):
    summerized_objective: str = Field(..., description="Core analysis objective")
    required_data: str = Field(..., description="Data or information needed for the analysis")

objective_summary_parser = PydanticOutputParser(pydantic_object=ObjectiveSummary)

# Prompt template
system_template = """
You will be given texts that is part of a business data analysis plan.

Please summarize:
- The core objective of the analysis
- What data (or tables) are likely needed to achieve it

Output the summary in JSON format in the following structure:
{format_instructions}
"""

human_template = """Text:
{analysis_text}
"""

objective_summary_prompt = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template(human_template)
    ],
    input_variables=["analysis_text"],
    partial_variables={"format_instructions": objective_summary_parser.get_format_instructions()}
)


# table recommendation prompt and parser
class TableRecommendation(BaseModel):
    table: str = Field(..., description="The table name")
    important_columns: List[str] = Field(..., description="List of important columns to focus on in this table")

class RecommendedTables(BaseModel):
    recommended_tables: List[TableRecommendation] = Field(..., description="List of recommended tables with key columns")
    analysis_method: str = Field(..., description="Step-by-step explanation of how to perform the analysis")
    
table_rec_parser = PydanticOutputParser(pydantic_object=RecommendedTables)


example = """
"""

system_template =  """
You are a senior data analyst assistant.
You will be provided with a user's business analysis objective and a list of available tables with their descriptions.

Your job is to:
- 1. Recommend the most relevant database tables needed to solve the objective (up to 10; fewer is fine). Order them by relevance.
- 2. For each table you recommend, list important columns that are most relevant to the analysis objective. Do not include all columns, just the key ones that are essential for the analysis.
- 3. Using the tables and columns above, describe a detailed step-by-step analysis process that directly addresses the stated objective. Number the steps in the analysis process.
- Your answer will be parsed by a strict JSON parser. Follow the exact output format.

Output Format:
{format_instructions}
"""

human_template = """
Analysis objective:
{objective}

Available Tables and descriptions:
{tables}
"""

table_rec_prompt = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template(human_template)
    ],
    input_variables=["objective", "tables"],
    partial_variables={"format_instructions": table_rec_parser.get_format_instructions()}
)