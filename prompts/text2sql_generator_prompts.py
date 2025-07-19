selector_template = """
As an experienced and professional database administrator, your task is to analyze a user question and a database schema to provide relevant information. 
The database schema consists of table descriptions, each containing multiple column descriptions. 
our goal is to identify the relevant tables and columns based on the user question and evidence provided.

[Instruction]:
1. Analyze the user question and evidence and decide what information is needed from the database schema. Think step by step.
2. Identify the relevant tables and columns that includes the information needed.
3. Discard any table or columns that is not related to the user question and evidence.
4. Sort the columns in each relevant table in descending order of relevance and keep the top 6 columns.
5. Ensure that at least 3 tables are included in the final output JSON.
6. The output should be in JSON format.

Requirements:
1. If a table has less than or equal to 5 columns, mark it as "keep_all".
2. If a table is completely irrelevant to the user question and evidence, mark it as "drop_all".
3. Prioritize the columns in each relevant table based on their relevance.

Here is a typical example:

==========
【DB_ID】 banking_system
【Schema】
# Table: account
Table description: Contains information about bank accounts, including account ID, district ID, frequency, and creation date.
[
  (account_id, the id of the account. Value examples: [11382, 11362, 2, 1, 2367].),
  (district_id, location of branch. Value examples: [77, 76, 2, 1, 39].),
  (frequency, frequency of the acount. Value examples: ['POPLATEK MESICNE', 'POPLATEK TYDNE', 'POPLATEK PO OBRATU'].),
  (date, the creation date of the account. Value examples: ['1997-12-29', '1997-12-28'].)
]
# Table: client
Table description: Contains personal information about clients.
[
  (client_id, the unique number. Value examples: [13998, 13971, 2, 1, 2839].),
  (gender, gender. Value examples: ['M', 'F']. And F：female . M：male ),
  (birth_date, birth date. Value examples: ['1987-09-27', '1986-08-13'].),
  (district_id, location of branch. Value examples: [77, 76, 2, 1, 39].)
]
# Table: loan
Table description: Contains information about loans that clients have taken.
[
  (loan_id, the id number identifying the loan data. Value examples: [4959, 4960, 4961].),
  (account_id, the id number identifying the account. Value examples: [10, 80, 55, 43].),
  (date, the date when the loan is approved. Value examples: ['1998-07-12', '1998-04-19'].),
  (amount, the id number identifying the loan data. Value examples: [1567, 7877, 9988].),
  (duration, the id number identifying the loan data. Value examples: [60, 48, 24, 12, 36].),
  (payments, the id number identifying the loan data. Value examples: [3456, 8972, 9845].),
  (status, the id number identifying the loan data. Value examples: ['C', 'A', 'D', 'B'].)
]
# Table: district
Table description: Contains information about districts, including district ID, area, number of inhabitants, literacy rate, number of entrepreneurs, cities, schools, hospitals, average salary, poverty rate, unemployment rate, and number of crimes.
[
  (district_id, location of branch. Value examples: [77, 76].),
  (A2, area in square kilometers. Value examples: [50.5, 48.9].),
  (A4, number of inhabitants. Value examples: [95907, 95616].),
  (A5, number of households. Value examples: [35678, 34892].),
  (A6, literacy rate. Value examples: [95.6, 92.3, 89.7].),
  (A7, number of entrepreneurs. Value examples: [1234, 1456].),
  (A8, number of cities. Value examples: [5, 4].),
  (A9, number of schools. Value examples: [15, 12, 10].),
  (A10, number of hospitals. Value examples: [8, 6, 4].),
  (A11, average salary. Value examples: [12541, 11277].),
  (A12, poverty rate. Value examples: [12.4, 9.8].),
  (A13, unemployment rate. Value examples: [8.2, 7.9].),
  (A15, number of crimes. Value examples: [256, 189].)
]
【Foreign keys】
client."district_id" = district."district_id"
【Question】
What is the gender of the youngest client who opened account in the lowest average salary branch?
【Evidence】
Later birthdate refers to younger age; A11 refers to average salary
【Answer】
```json
{{
  "account": "keep_all",
  "client": "keep_all",
  "loan": "drop_all",
  "district": ["district_id", "A11", "A2", "A4", "A6", "A7"]
}}
```
Question Solved.

==========

Here is a new example, please start answering:

【DB_ID】 {db_id}
【Schema】
{desc_str}
【Foreign keys】
{fk_str}
【Question】
{query}
【Evidence】
{evidence}
【Answer】
"""


# Need to modify if using another DB
decompose_template = """
Given a 【Database schema】 description, a knowledge 【Evidence】 and the 【Question】, you need to use valid POSTGRESQL and understand the database and knowledge, and then decompose the question into subquestions for text-to-SQL generation.
When generating SQL, we should always consider constraints:
【Constraints】
- In SELECT <column>, just select needed columns in the 【Question】 without any unnecessary column or value
- In FROM <table> or JOIN <table>, do not include unnecessary table
- If use max or min func, JOIN <table> FIRST, THEN use SELECT MAX(<column>) or SELECT MIN(<column>)
- If [Value examples] of <column> has 'None' or None, use JOIN <table> or WHERE <column> IS NOT NULL is better
- If use ORDER BY <column> ASC|DESC, add GROUP BY <column> before to select distinct values
==========

【Database schema】
# Table: frpm
[
  ("CDSCode", "CDSCode". Value examples: ['01100170109835', '01100170112607'].),
  ("Charter School (Y/N)", "Charter School (Y/N)". Value examples: [1, 0, NULL]. And 0: N;. 1: Y),
  ("Enrollment (Ages 5-17)", "Enrollment (Ages 5-17)". Value examples: [5271.0, 4734.0].),
  ("Free Meal Count (Ages 5-17)", "Free Meal Count (Ages 5-17)". Value examples: [3864.0, 2637.0]. And eligible free rate = Free Meal Count / Enrollment)
]
# Table: satscores
[
  ("cds", "California Department Schools". Value examples: ['10101080000000', '10101080109991'].),
  ("sname", "school name". Value examples: ['None', 'Middle College High', 'John F. Kennedy High', 'Independence High', 'Foothill High'].),
  ("NumTstTakr", "Number of Test Takers in this school". Value examples: [24305, 4942, 1, 0, 280]. And number of test takers in each school),
  ("AvgScrMath", "average scores in Math". Value examples: [699, 698, 289, NULL, 492]. And average scores in Math),
  ("NumGE1500", "Number of Test Takers Whose Total SAT Scores Are Greater or Equal to 1500". Value examples: [5837, 2125, 0, NULL, 191]. And Number of Test Takers Whose Total SAT Scores Are Greater or Equal to 1500. . commonsense evidence:. . Excellence Rate = NumGE1500 / NumTstTakr)
]
【Foreign keys】
frpm."CDSCode" = satscores."cds"
【Question】
List school names of charter schools with an SAT excellence rate over the average.
【Evidence】
Charter schools refers to "Charter School (Y/N)" = 1 in the table frpm; Excellence rate = NumGE1500 / NumTstTakr


Decompose the question into sub questions, considering 【Constraints】, and generate the SQL after thinking step by step:
Sub question 1: Get the average value of SAT excellence rate of charter schools.
SQL
```sql
SELECT AVG(CAST(T2."NumGE1500" AS float) / T2."NumTstTakr")
    FROM frpm AS T1
    INNER JOIN satscores AS T2
    ON T1."CDSCode" = T2."cds"
    WHERE T1."Charter School (Y/N)" = 1
```

Sub question 2: List out school names of charter schools with an SAT excellence rate over the average.
SQL
```sql
SELECT T2."sname"
  FROM frpm AS T1
  INNER JOIN satscores AS T2
  ON T1."CDSCode" = T2."cds"
  WHERE T2."sname" IS NOT NULL
  AND T1."Charter School (Y/N)" = 1
  AND CAST(T2."NumGE1500" AS float) / T2."NumTstTakr" > (
    SELECT AVG(CAST(T4."NumGE1500" AS float) / T4."NumTstTakr")
    FROM frpm AS T3
    INNER JOIN satscores AS T4
    ON T3."CDSCode" = T4."cds"
    WHERE T3."Charter School (Y/N)" = 1
  )
```

Question Solved.

==========

【Database schema】
# Table: account
[
  ("account_id", "the id of the account". Value examples: [11382, 11362, 2, 1, 2367].),
  ("district_id", "location of branch". Value examples: [77, 76, 2, 1, 39].),
  ("frequency", "frequency of the account". Value examples: ['POPLATEK MESICNE', 'POPLATEK TYDNE', 'POPLATEK PO OBRATU'].),
  ("date", "the creation date of the account". Value examples: ['1997-12-29', '1997-12-28'].)
]
# Table: client
[
  ("client_id", "the unique number". Value examples: [13998, 13971, 2, 1, 2839].),
  ("gender", "gender". Value examples: ['M', 'F']. And F：female . M：male ),
  ("birth_date", "birth date". Value examples: ['1987-09-27', '1986-08-13'].),
  ("district_id", "location of branch". Value examples: [77, 76, 2, 1, 39].)
]
# Table: district
[
  ("district_id", "location of branch". Value examples: [77, 76, 2, 1, 39].),
  ("A4", "number of inhabitants". Value examples: ['95907', '95616', '94812'].),
  ("A11", "average salary". Value examples: [12541, 11277, 8114].)
]
【Foreign keys】
account."district_id" = district."district_id"
client."district_id" = district."district_id"
【Question】
What is the gender of the youngest client who opened account in the lowest average salary branch?
【Evidence】
Later birthdate refers to younger age; A11 refers to average salary

Decompose the question into sub questions, considering 【Constraints】, and generate the SQL after thinking step by step:
Sub question 1: What is the district_id of the branch with the lowest average salary?
SQL
```sql
SELECT "district_id"
  FROM district
  ORDER BY "A11" ASC
  LIMIT 1
```

Sub question 2: What is the youngest client who opened account in the lowest average salary branch?
SQL
```sql
SELECT T1."client_id"
  FROM client AS T1
  INNER JOIN district AS T2
  ON T1."district_id" = T2."district_id"
  ORDER BY T2."A11" ASC, T1."birth_date" DESC 
  LIMIT 1
```

Sub question 3: What is the gender of the youngest client who opened account in the lowest average salary branch?
SQL
```sql
SELECT T1."gender"
  FROM client AS T1
  INNER JOIN district AS T2
  ON T1."district_id" = T2."district_id"
  ORDER BY T2."A11" ASC, T1."birth_date" DESC 
  LIMIT 1 
```
Question Solved.

==========

【Database schema】
{desc_str}
【Foreign keys】
{fk_str}
【Question】
{query}
【Evidence】
{evidence}

Decompose the question into sub questions, considering 【Constraints】, and generate the SQL after thinking step by step:
"""


refiner_template = """
【Instruction】
When executing SQL below, some errors occurred, please fix up SQL based on query and database info.
Solve the task step by step if you need to.
When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible.

【Constraints】
- In SELECT <column>, just select needed columns in the 【Question】 without any unnecessary column or value
- In FROM <table> or JOIN <table>, do not include unnecessary table
- If use max or min func, JOIN <table> FIRST, THEN use SELECT MAX(<column>) or SELECT MIN(<column>)
- If [Value examples] of <column> has 'None' or None, use JOIN <table> or WHERE <column> IS NOT NULL is better
- If use ORDER BY <column> ASC|DESC, add GROUP BY <column> before to select distinct values

【Query】
-- {query}
【Evidence】
{evidence}
【Database info】
{desc_str}
【Foreign keys】
{fk_str}
【old SQL】
```sql
{sql}
```
【POSTGRESQL error】 
{sql_error}
【Exception class】
{exception_class}

Now please fixup old SQL and generate new SQL again. Only output the new SQL in the code block, and indicate script type by ```sql ```in the code block.
【correct SQL】
"""

refiner_feedback_template = """
【Instruction】
When executing SQL below, no rows were returned. please fix up SQL based on query, database info, and feedback on the old SQL.
Solve the task step by step if you need to.
When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible.

【Constraints】
- In SELECT <column>, just select needed columns in the 【Question】 without any unnecessary column or value
- In FROM <table> or JOIN <table>, do not include unnecessary table
- If use max or min func, JOIN <table> FIRST, THEN use SELECT MAX(<column>) or SELECT MIN(<column>)
- If [Value examples] of <column> has 'None' or None, use JOIN <table> or WHERE <column> IS NOT NULL is better
- If use ORDER BY <column> ASC|DESC, add GROUP BY <column> before to select distinct values
【Query】
-- {query}
【Evidence】
{evidence}
【Database info】
{desc_str}
【Foreign keys】
{fk_str}

【Feedback】
{review_feedback}
【old SQL】
```sql
{sql}
```

Now please fixup old SQL and generate new SQL again. Only output the new SQL in the code block, and indicate script type by ```sql ```in the code block.
【correct SQL】
"""


review_noresult_template = """
You generated the following SQL for a user's question. The query executed, but no rows were returned.

Your job is to determine:
- Is the SQL logically correct, meaning the structure and filter logic are appropriate for the user's question?
- Or is there a mistake in the SQL that, if corrected, would likely return results?

[Instructions]
- If the SQL logic is sound and the absence of rows is likely due to a lack of matching data, respond only with: `Yes.`
- If the SQL has a logical issue (e.g., wrong JOINs, incorrect filters, misused columns) that could explain the lack of results, respond **only** with: `No. <brief explanation>`

-------

Examples:

1.  
User Question: "Show all orders from last month."  
SQL:  
SELECT * FROM orders 
WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month' 
AND created_at < DATE_TRUNC('month', CURRENT_DATE);  
Output: Yes.  
(The SQL logic is correct and filters for the previous month. If there are no matching rows, it's a data issue, not a query issue.)

2. 
User Question: “Which users purchased groceries this year?”
SQL:
SELECT u.user_id  
FROM users u  
JOIN orders o ON u.user_id = o.user_id  
JOIN order_items oi ON o.order_id = oi.order_id  
JOIN products p ON oi.sku_id = p.product_id  
JOIN categories c ON p.category_id = c.category_id  
WHERE c.name = 'Groceries' AND EXTRACT(YEAR FROM o.created_at) = EXTRACT(YEAR FROM CURRENT_DATE)  
Output: No. The join condition on oi.sku_id = p.product_id is incorrect. It should likely be oi.sku_id = s.sku_id JOINED to sku and then to products.

--------

Now analyze the following SQL and answer using the same format. Use the shema information provided to determine if the SQL logic is sound.:

User Question: {query}
SQL: {sql}
schema info: {desc_str}
evidence: {evidence}

Output Format:
Yes.
No. <explanation of the logical issue>

Note: Do NOT say 'No.' if the SQL logic is sound but the data may be missing. That should be answered with 'Yes.'
"""


review_result_template = """
You generated an SQL for a user's question. The query executed successfully and returned results.
Your job is to determine:

If the result is sufficient and well-matched to the user's question, answer 'Yes'.
If not, answer 'No' and provide an explanation of why the answer is insufficient.

User question: {query}
SQL result: {result}

Output Format:
Yes.
No. <explanation of why the answer is insufficient>
"""

