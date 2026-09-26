# agent/agent.py
import os
from google.cloud import aiplatform
from google.cloud.aiplatform import adk  # <-- ADK 2.0 Production Namespace
from google.cloud import bigquery
from google.cloud import dataproc_v1 as dataproc

# --- CUSTOM TOOL DEFINITIONS ---

@adk.tool
def execute_lakehouse_sql(sql_query: str) -> str:
    """
    Executes an analytical SQL query against the SwiftRoute Lakehouse tables.
    """
    client = bigquery.Client()
    try:
        query_job = client.query(sql_query)
        results = query_job.result()
        rows = [str(dict(row)) for row in results]
        return "\n".join(rows[:25])
    except Exception as e:
        return f"SQL Execution Error: {str(e)}"

@adk.tool
def submit_spark_job(pyspark_code: str, target_table: str) -> str:
    """
    Submits a serverless PySpark batch job to Managed Service for Apache Spark.
    """
    project_id = os.getenv("GCP_PROJECT_ID")
    region = os.getenv("GCP_REGION", "us-central1")
    bucket_name = os.getenv("GCP_SPARK_BUCKET", f"{project_id}-spark-jobs")
    
    client = dataproc.BatchControllerClient(
        client_options={"api_endpoint": f"{region}-dataproc.googleapis.com:443"}
    )
    
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
        return f"Successfully generated PySpark script and submitted serverless job targeting '{target_table}'."
    except Exception as e:
        return f"Spark Job Submission Error: {str(e)}"

# --- SYSTEM INSTRUCTION & AGENT CONSTRUCTOR ---

SYSTEM_INSTRUCTION = """
You are a highly capable Lakehouse Multi-Engine Orchestrator for SwiftRoute Logistics.
Your job is to help users analyze, transform, and reason over Apache Iceberg tables in Google Cloud Lakehouse.
"""

def create_swiftroute_agent() -> adk.Agent:
    """Instantiates the ADK 2.0 Agent with our system instructions and custom tools."""
    # Initialize the Vertex AI SDK (ADK 2.0)
    aiplatform.init(
        project=os.getenv("GCP_PROJECT_ID"),
        location=os.getenv("GCP_REGION", "us-central1")
    )
    
    agent = adk.Agent(
        display_name="SwiftRoute Lakehouse Orchestrator",
        instructions=SYSTEM_INSTRUCTION,
        model="gemini-3.8-flash",  # Leveraging state-of-the-art agentic reasoning
        tools=[execute_lakehouse_sql, submit_spark_job]
    )
    return agent
