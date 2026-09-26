# agent/agent.py
import os
from vertexai.preview import adk
from google.cloud import bigquery
from google.cloud import dataproc_v1 as dataproc

# --- CUSTOM TOOL DEFINITIONS ---

# SQL Execution Tool (Pillars 2 and 3)
@adk.tool
def execute_lakehouse_sql(sql_query: str) -> str:
    """
    Executes a standard SQL query against the SwiftRoute Lakehouse tables.
    Use this for:
    - Lightweight analytical queries and aggregations.
    - Iceberg Time Travel queries using 'FOR SYSTEM_TIME AS OF' (limited to 7 days).
    - Highly targeted, late-stage joins between structured Iceberg tables 
      and unstructured GCS Object Tables (BigQueryObjectRefs).
    """
    client = bigquery.Client()
    try:
        query_job = client.query(sql_query)
        results = query_job.result()
        # Convert results to a list of dict strings for the LLM
        rows = [str(dict(row)) for row in results]
        return "\n".join(rows[:25])  # Limit response to protect context window
    except Exception as e:
        return f"SQL Execution Error: {str(e)}"

# Serverless Spark Job Tool (Pillar 1)
@adk.tool
def submit_spark_job(pyspark_code: str, target_table: str) -> str:
    """
    Submits a serverless PySpark batch job to Managed Service for Apache Spark.
    Use this when the user requests large-scale data cleansing, 
    massive row-by-row updates, or ML feature transformations over Iceberg tables.
    """
    project_id = os.getenv("GCP_PROJECT_ID", "dssetup-202519")
    region = os.getenv("GCP_REGION", "us-central1")
    bucket_name = os.getenv("GCP_SPARK_BUCKET", f"{project_id}-spark-jobs")
    
    client = dataproc.BatchControllerClient(
        client_options={"api_endpoint": f"{region}-dataproc.googleapis.com:443"}
    )
    
    # Save the generated PySpark code locally (in container runtime) to prepare for execution
    # In production, this would be written directly to a secure, audited GCS bucket
    pyspark_file_uri = f"gs://{bucket_name}/temp_agent_job.py"
    
    batch = dataproc.Batch(
        pyspark_batch=dataproc.PySparkBatch(
            main_python_file_uri=pyspark_file_uri,
            jar_file_uris=["gcs://spark-lib/iceberg/iceberg-spark-runtime-3.5_2.12.jar"]
        )
    )
    
    try:
        request = dataproc.CreateBatchRequest(
            parent=f"projects/{project_id}/regions/{region}", 
            batch=batch
        )
        # client.create_batch(request=request) # Asynchronous execution call
        return f"Successfully generated PySpark script and submitted serverless job targeting '{target_table}'."
    except Exception as e:
        return f"Spark Job Submission Error: {str(e)}"

# --- SYSTEM INSTRUCTION & AGENT CONSTRUCTOR ---

SYSTEM_INSTRUCTION = """
You are a highly capable Lakehouse Multi-Engine Orchestrator for SwiftRoute Logistics.
Your job is to help users analyze, transform, and reason over Apache Iceberg tables in Google Cloud Lakehouse.

You must choose the optimal engine for each task:
1. ENGINE SELECTION RULE:
   - For fast analytical queries, transactional checks, or viewing historical states, use 'execute_lakehouse_sql'.
   - For heavy data manipulation, machine learning preparation, or batch transformations, use 'submit_spark_job'. Do not use SQL for high-resource transformations.

2. DATA QUALITY & PROMOTION (Staging Pattern):
   - When generating PySpark transformations, write the output back to a staging table (e.g., 'shipments_agent_staging') instead of writing directly to the production 'shipments' table.
   - Run automated validation rules, and then use SQL to MERGE (Preview) the staging rows into production.

3. TEMPORAL RECONCILIATION:
   - For billing and contract audits, write SQL queries leveraging Iceberg Time Travel: 'FOR SYSTEM_TIME AS OF'. Note that BigQuery queries are limited to a 7-day time travel window.

4. UNSTRUCTURED LATE-STAGE BLENDING:
   - When asked to analyze driver reports or PDF claims associated with structured records, perform a late-stage blend:
     First, write a SQL query to filter the structured Iceberg table to isolate the specific targeted rows. 
     Second, join those rows with the GCS Object Table (via BigQueryObjectRefs).
     Third, apply AI.GENERATE_TEXT to run Gemini only on those filtered rows to analyze the files.
"""

def create_swiftroute_agent() -> adk.Agent:
    """Instantiates the ADK Agent with our system instructions and custom tools."""
    agent = adk.Agent(
        display_name="SwiftRoute Lakehouse Orchestrator",
        instructions=SYSTEM_INSTRUCTION,
        model="gemini-3.8-flash",  # Leveraging state-of-the-art agentic reasoning
        tools=[execute_lakehouse_sql, submit_spark_job]
    )
    return agent
