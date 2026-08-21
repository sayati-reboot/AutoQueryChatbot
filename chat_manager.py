from llm_planner import execution_plan
from query_db import query_db
from generate_report import generate_report

def process_manager(query):
    # Generate execution plan
    plan = execution_plan(query)
    
    #query the database if user intent is query
    if plan['intent'] == 'query':
        results = query_db(plan['sql_query'])
        return {
            'type': 'text',
            'results': results
        }
    # Generate a report based on the query results
    if plan['intent'] == 'report':
        results = query_db(plan['sql_query'])
        report = generate_report(results)
        return {
            'type': 'file',
            'results': report
        }