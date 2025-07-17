from typing import Dict
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate


class TableMetaData(BaseModel):
    description: str = Field(..., description="Description of the table")
    columns: Dict[str, str] = Field(..., description="Details about columns")
    sample_usage: list[str] = Field(..., description="Example usages of this table in data analysis")

parser = PydanticOutputParser(pydantic_object=TableMetaData)

system_template = """You are an expert in analyzing database structures and generating metadata for a single table.
You will be given a schema extracted from PostgreSQL, describing a single table.

Generate:
1. A natural language description of the table (description)
2. A dictionary of columns with detailed desciptions (columns)
3. One or two example use cases of how the table can be used in data analysis (sample_usage)

Output must be a JSON object:
{format_instructions}
"""

human_template = """Table schema:
{schema}
"""

prompt = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template(human_template)
    ],
    input_variables=["schema"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)