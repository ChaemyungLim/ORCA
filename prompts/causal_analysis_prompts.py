from typing import List, Optional
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


### 1. Causal Question Parsing Prompt
class ParsedCausalQuery(BaseModel):
    treatment: str
    treatment_expression: str
    outcome: str
    outcome_expression: str
    confounders: List[str]
    confounder_expressions: List[str]
    mediators: List[str] = []
    instrumental_variables: List[str] = []
    
parse_query_parser = PydanticOutputParser(pydantic_object=ParsedCausalQuery)

parse_query_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a expert data analyst for causal inference.

Given a natural language question, table descriptions and an expression_dict, extract:

- treatment: variable being manipulated
- outcome: variable being affected
- treatment_expression / outcome_expression: SQL expression to compute the variable (may include CASE WHEN, math functions, etc.)
- confounders: control variables for backdoor adjustment
- confounder_expressions: SQL expressions for each confounder (same order)
- mediators: optional variables on the causal path
- instrumental_variables: optional IVs

# Rules:
- Use only columns or derivable expressions from the schema.
- Do NOT use identifiers like *_id or primary keys as variables.
- If a variable (e.g., age) needs to be derived, define an alias (e.g., "age") and include its SQL expression in confounder_expressions.
- Expressions must match SQL syntax (e.g., CASE WHEN ..., DATE_PART(...), etc.)
- Refer to the provided expression_dict to reuse known SQL expressions instead of writing from scratch.
- Do not use table aliases (e.g., cu, r). Use full column names.

Return in JSON format.
{format_instructions}
"""),
    ("human", """
Question:
{question}

Table Descriptions:
{tables}

If helpful, here is a dictionary mapping variable names to SQL expressions:
{expression_dict}
""")
]).partial(format_instructions=parse_query_parser.get_format_instructions())

### 2. SQL Generation Prompt
class GeneratedSQL(BaseModel):
    sql_query: str = Field(..., description="A valid SQL query to fetch data for causal analysis")

sql_query_parser = PydanticOutputParser(pydantic_object=GeneratedSQL)

sql_generation_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a senior data analyst generating a SQL query for causal analysis.

You are given:
- A list of variable names that appear in the causal graph.
- A mapping from each variable to its SQL expression.
   - ⚠️ These expressions may include unsafe patterns such as correlated subqueries.
        Do not blindly copy them into the SELECT clause.
        Instead, transform them into JOIN-based expressions if they rely on values from other tables.
- Full schema descriptions.

Write a SQL query that:
- SELECTs each expression using `AS variable_name`
- Joins all required tables using valid foreign keys
- Returns a flat, analysis-ready table

## Rules:
- Do not include explanatory text
- Use only columns and tables from the schema
- Do not alias tables (e.g., avoid `FROM users u`)
- Do not include GROUP BY or ORDER BY unless needed
- All expressions must be valid SQL syntax (e.g., DATE_PART, COALESCE, CASE WHEN)

- NEVER write expressions like `(SELECT ... WHERE ... = outer_column LIMIT 1)`, as they will result in 'correlated subquery' errors in PostgreSQL.
- For Boolean flags based on lookup tables (e.g., "used_coupon" from "coupon_usage"), precompute them via LEFT JOIN subqueries using DISTINCT or GROUP BY, and assign the Boolean directly (e.g., TRUE AS used_coupon).
- All SELECT expressions must refer to columns or aliases available in the FROM/JOIN scope.

{format_instructions}
"""),
    ("human", """
Variables to Select:
{selected_variables}

Expressions:
{variable_expressions}

Table Schemas:
{table_schemas}
""")
]).partial(format_instructions=sql_query_parser.get_format_instructions())

### 3. SQL Fix Prompt (on failure)

class FixedSQL(BaseModel):
    sql_query: str = Field(..., description="A revised valid SQL query that resolves the original error")

fix_sql_parser = PydanticOutputParser(pydantic_object=FixedSQL)

fix_sql_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a senior data analyst. Your task is to revise a faulty SQL query based on the error message returned during execution.

You will be given:
1. The original SQL query
2. The error message it triggered
3. A list of variable names to select and corresponding SQL expressions
4. Table schemas

Your job is to modify the SQL query to resolve the error while preserving the original intent: 
fetching all listed variables using their SQL expressions.

Be sure to:
- Correct incorrect column names or aliases
- Fix joins if necessary
- SELECT each expression as the `variable_name` using `AS`
- Ensure the result includes all specified variables
- Use only tables and columns from the provided schema
- When using aggregate functions (e.g., AVG, COUNT), ensure that all other selected columns are either:
  - included in the GROUP BY clause, or
  - wrapped inside an aggregate function
- CASE WHEN expressions are not aggregate functions and must be included in GROUP BY or aggregated

- NEVER write expressions like `(SELECT ... WHERE ... = outer_column LIMIT 1)`, as they will result in 'correlated subquery' errors in PostgreSQL.
- For Boolean flags based on lookup tables (e.g., "used_coupon" from "coupon_usage"), precompute them via LEFT JOIN subqueries using DISTINCT or GROUP BY, and assign the Boolean directly (e.g., TRUE AS used_coupon).
- All SELECT expressions must refer to columns or aliases available in the FROM/JOIN scope.

{format_instructions}
"""),
    ("human", """
Original SQL Query:
```sql
{original_sql}
```

Error Message:
```
{error_message}
```
Variables to Select:
{graph_nodes}

Variable Expressions:
{expression_dict}

Table Schemas:
{table_schemas}
""")
]).partial(format_instructions=fix_sql_parser.get_format_instructions())

## 4. Causal Strategy Selection Prompt
class SelectedCausalStrategy(BaseModel):
    causal_task: str = Field(..., description="Overall causal task (e.g., estimating_causal_effect, mediation_analysis, causal_prediction, what_if)")
    identification_strategy: str = Field(..., description="Strategy used to identify the causal effect, e.g., backdoor, frontdoor, iv, mediation")
    estimation_method: str = Field(..., description="Estimation method compatible with identification strategy")
    refutation_methods: List[str] = Field(..., description="Optional refutation methods to test robustness")

strategy_output_parser = PydanticOutputParser(pydantic_object=SelectedCausalStrategy)

causal_strategy_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a causal inference expert using the DoWhy library.

Your job is to choose the appropriate causal inference strategy, estimation method, and optional refutation methods given:
- A user's causal question
- Extracted variables (treatment, outcome, confounders)
    - data type information as `{treatment_type}` and `{outcome_type}`
- Basic data preview

Only choose from the valid options defined below.

---
Causal Tasks:
- estimating_causal_effect: estimate average treatment effect (ATE)
- mediation_analysis: decompose effect via mediators
- causal_prediction: predict outcome using causal structure (e.g., TabPFN)
- what_if: simulate counterfactuals
- root_cause: identify potential causes of outcome

Identification Strategies:
- backdoor: adjust for confounders that affect both treatment and outcome
- frontdoor: identify effect using mediators when backdoor not available
- iv: use instrumental variables for exogenous variation
- mediation: isolate indirect vs direct effects
- id_algorithm: automated graphical ID algorithm

- If outcome_type is "binary", prefer using backdoor.generalized_linear_model
- If outcome_type is "continuous", prefer using backdoor.linear_regression

Estimation Methods:
- backdoor.linear_regression: basic OLS on adjusted data
- backdoor.propensity_score_matching: match units by treatment probability
- backdoor.propensity_score_stratification: stratify by score and estimate
- backdoor.propensity_score_weighting: reweight sample by inverse propensity
- backdoor.distance_matching: match using nearest-neighbor distance
- backdoor.generalized_linear_model: GLM for non-normal outcomes
- iv.instrumental_variable: two-stage least squares using IV
- iv.regression_discontinuity: exploit cutoff-based variation
- frontdoor.two_stage_regression: mediator-based 2-stage estimator
- mediation.two_stage_regression: mediation-specific 2-stage model
- causal_prediction.tabpfn: use TabPFN to predict causal outcomes
- what_if.simple_model: simulate counterfactual with regression
- what_if.tabpfn: simulate counterfactual using TabPFN

Refutation Methods (optional):
- placebo_treatment_refuter: randomly replace treatment and re-test
- random_common_cause: add synthetic common cause to check stability
- data_subset_refuter: re-run analysis on subsets
- add_unobserved_common_cause: simulate bias from unobserved variables

{format_instructions}
"""),
    ("human", """
User Causal Question:
{question}

Parsed Variables:
- Treatment: {treatment}
- Outcome: {outcome}
- Confounders: {confounders}
- Mediators: {mediators}
- Instrumental Variables: {instrumental_variables}

Data Sample:
{df_sample}

Treatment Type: {treatment_type}
Outcome Type: {outcome_type}
""")
]).partial(format_instructions=strategy_output_parser.get_format_instructions())

## 5. Causal Analysis Result Generation Prompt
class CausalResultExplanation(BaseModel):
    explanation: str = Field(..., description="Plain-text summary of the causal analysis results.")

generate_answer_parser = PydanticOutputParser(pydantic_object=CausalResultExplanation)

generate_answer_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a causal inference expert. Based on the following information, write a clear but informative explanation of the causal analysis results.

Causal task metadata:
- Task type: {task}
- Estimator used: {estimation_method}
- Estimated causal effect: {causal_effect_value}
- 95% confidence interval: {causal_effect_ci}
- p-value (if available): {causal_effect_p_value}
- Refutation result (if any): {refutation_result}
- Label mappings (optional): {label_maps}

Parsed query details:
- Treatment variable: {treatment} — {treatment_expression_description}
- Outcome variable: {outcome} — {outcome_expression_description}
- Confounders: {confounders}
- Mediators (if any): {mediators}
- Instrumental variables (if any): {instrumental_variables}
- Additional notes: {additional_notes}
- Main table: {main_table}
- Join tables: {join_tables}

Your explanation should include:
1. Interpretation of the estimated effect,
2. Whether the effect is statistically significant based on p-value or CI,
3. Whether the refutation result strengthens or weakens confidence in the finding,
4. Any caveats or assumptions that should be kept in mind,
5. If label mappings are provided, interpret the effect in human terms.

Respond with a concise analytical summary (3–6 sentences).

{format_instructions}
"""),
    ("human", "")
]).partial(format_instructions=generate_answer_parser.get_format_instructions())


sql_reconstructor_parser = StrOutputParser()
sql_reconstruct_prompt = ChatPromptTemplate.from_messages([
    ("system", """
 You are a SQL reconstruction assistant. Your task is to generate a **valid and executable SQL query** that evaluates the given expression using correct FROM and JOIN clauses.

### Requirements:
1. **DO NOT change the expression itself.** Keep it exactly as given.  
   - Exception: If the expression contains invalid SQL (e.g., nonexistent column/function), you must correct it using the provided table schemas.

2. Use only table and column names that exist in the `table_schemas`.  
   - If a column contains special characters or spaces (e.g., `Charter School (Y/N)`), wrap it in double quotes: `"Charter School (Y/N)"`.

3. All table references in expressions must be joined in the FROM clause.  
   - Do not reference a table unless it is included in `main_table` or `join_tables`.

4. If using functions like `YEAR()`, `MONTH()`, etc., verify that they are valid in standard SQL.  
   - If `YEAR(date_column)` is not valid, rewrite as `EXTRACT(YEAR FROM date_column)`.

5. Do not use columns in SELECT that are not aggregated or grouped.  
   - If the expression uses subqueries or aggregate functions, and a column is not aggregated, either wrap it in an aggregate or include it in a GROUP BY clause only if needed.

6. If disambiguation is needed due to duplicate column names, prefix with the appropriate table name from the schema.

7. If any table aliases are required, define and use them explicitly and consistently.  
   - Do not reference undefined aliases (e.g., using "ha" for "hero_attribute" without declaring it).

8. If a column appears in the expression but not in the schema, attempt to infer the correct table.column name based on the schema.  
   - For example, if `"gender"` is not found, but `"superhero.gender_id"` exists, rewrite accordingly.

### Output Format:
Return a **minimal SQL query** in the form:

SELECT <expression> AS result
FROM ...
JOIN ...

- Do not wrap your output in markdown (no ```sql blocks).
- Return the SQL query as plain text only.
Do not include GROUP BY or ORDER BY unless strictly necessary to make the query valid.

Ensure that:
	•	All table and column names exist in the schema.
	•	The expression is syntactically valid.
	•	The result is a single-column query with alias result.

"""),
    ("human", """
Given the following inputs, reconstruct the full SQL query wrapping the expression using a correct FROM and JOIN clause:

Expression:
{expression}

Main Table:
{main_table}

Join Tables:
{join_tables}

Original SQL Query:
{sql_query}

Table Schemas:
{table_schemas}

Your output must only include the final SQL query.
""")
])