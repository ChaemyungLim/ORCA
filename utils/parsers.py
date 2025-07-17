import json
import re


def parse_sql_from_string(input_string):
    sql_pattern = r'```sql(.*?)```'
    all_sqls = []
    for match in re.finditer(sql_pattern, input_string, re.DOTALL):
        all_sqls.append(match.group(1).strip())
    if all_sqls:
        return all_sqls[-1]
    else:
        return "error: No SQL found in the input string"


def parse_json_from_string(res):
    m = re.search(r"```json\s*([\s\S]+?)```", res)
    if not m:
        m = re.search(r"```([\s\S]+?)```", res)
    if m:
        res = m.group(1).strip()
    return json.loads(res)