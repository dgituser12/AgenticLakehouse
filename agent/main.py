# agent/agent.py
import os
from google.cloud import aiplatform
from google.cloud import bigquery
from google.cloud import storage
from google.cloud import dataproc_v1 as dataproc

# Import the official, validated ADK classes
from google.adk.agents.llm_agent import LlmAgent as Agent
from google.adk.tools import FunctionTool

# Verified MCP Classes & Namespaces for ADK 2.0
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

# --- 1. MODEL CONTEXT PROTOCOL (MCP) DISCOVERY SETUP ---

def get_knowledge_catalog_mcp_toolset():
    """
    Connects to the native Knowledge Catalog MCP Tool Server over HTTP/SSE.
    Returns the McpToolset instance directly.
    """
    project_id = os.getenv("GCP_PROJECT_ID")
    region = os.getenv("GCP_REGION", "us-central1")
    
    # Instantiate McpToolset synchronously using StreamableHTTPConnectionParams
    catalog_toolset = McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=f"https://dataplex.googleapis.com/v1/projects/{project_id}/locations/{region}/mcpServers/default"
        )
    )
    
    return catalog_toolset

# --- 2. CUSTOM DATA EXECUTION FUNCTIONS ---

def execute_lakehouse_sql(sql_query: str) -> str:
    """
    Executes an analytical SQL query against the SwiftRoute Lakehouse tables.
    Use this for:
    - Lightweight analytical queries and aggregations.
    - Iceberg Time Travel queries using 'FOR SYSTEM_TIME AS OF' (limited to 7 days).
    - Highly targeted, late-stage joins between structured Iceberg tables 
      and unstructured GCS Object Tables (BigQueryObjectRefs).
    """
    # AUTOMATIC DRY-RUN FALLBACK
    if os.getenv("LAKEHOUSE_DRY_RUN", "true").lower() == "true":
        print(f"\n⚡ [DRY-RUN SQL]: Simulating execution of query:\n{sql_query}")
        # Return a realistic mock response matching the target scenario's output structure
        if "FOR SYSTEM_TIME AS OF" in sql_query:
            return "[{'status': 'PENDING', 'current_count': 142, 'historical_count': 124, 'drift': 18}]"
        elif "unstructured_claims" in sql_query:
            return "[{'transaction_id': 'TRX-10', 'customer_id': '10', 'amount': 5230.50, 'dispute_reason_summary': 'Cargo shifted during transit'}]"
        return "Dry-Run Success: SQL query executed. Isolated target dataset."
        
    # Physical Execution Path
    client = bigquery.Client()
    try:
        query_job = client.query(sql_query)
        results = query_job.result()
        # Convert results to a list of dict strings for the LLM
        rows = [str(dict(row)) for row in results]
        return "\n".join(rows[:25])  # Limit response to protect context window
    except Exception as e:
        return f"SQL Execution Error: {str(e)}"

def submit_spark_job(pyspark_code: str, target_table: str) -> str:
    """
    Submits a serverless PySpark batch job to Managed Service for Apache Spark.
    """
    # AUTOMATIC DRY-RUN FALLBACK
    if os.getenv("LAKEHOUSE_DRY_RUN", "true").lower() == "true":
        print(f"\n⚡ [DRY-RUN SPARK]: Simulating GCS script upload and Serverless Batch submission of code:\n{pyspark_code}")
        return f"Dry-Run Success: Generated PySpark script, simulated GCS upload, and submitted serverless job targeting '{target_table}'."

    # Physical Execution Path
    project_id = os.getenv("GCP_PROJECT_ID")
    region = os.getenv("GCP_REGION", "us-central1")
    bucket_name = os.getenv("GCP_SPARK_BUCKET", f"{project_id}-spark-jobs")
    
    # 1. Physically write the generated PySpark code to GCS
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob("temp_agent_job.py")
        blob.upload_from_string(pyspark_code)
        print(f"\n[GCS] Successfully uploaded PySpark script to gs://{bucket_name}/temp_agent_job.py")
    except Exception as e:
        return f"Failed to upload PySpark script to GCS: {str(e)}"
    
    # 2. Physically submit the batch job to Dataproc
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
        operation = client.create_batch(request=request)
        batch_id = operation.metadata.batch_id
        
        return f"Successfully generated PySpark script, uploaded to GCS, and physically submitted Serverless Batch job '{batch_id}' to Dataproc."
    except Exception as e:
        return f"Spark Job Submission Error: {str(e)}"

# --- 3. SYSTEM INSTRUCTION & AGENT CONSTRUCTOR ---

SYSTEM_INSTRUCTION = """
You are a highly capable Lakehouse Multi-Engine Orchestrator for SwiftRoute Logistics.
Your job is to help users analyze, transform, and reason over Apache Iceberg tables in Google Cloud Lakehouse.

CRITICAL DIRECTIVE:
Do not just write or display PySpark code or SQL queries in your text response if you have a tool that can execute them. 
You MUST call the appropriate tool ('submit_spark_job' or 'execute_lakehouse_sql') to perform the action. 
Only output code in markdown if you are explaining what you have already successfully executed via a tool.

You must choose the optimal engine for each task:
1. DATA DISCOVERY:
   - Always run 'search_entries' first to discover assets.
   - Use 'lookup_entry' and then 'lookup_context' to retrieve schema details, business glossaries, 
     and sample SQL patterns for the discovered tables.

2. ENGINE SELECTION RULE:
   - For fast analytical queries, transactional checks, or viewing historical states, use 'execute_lakehouse_sql'.
   - For heavy data manipulation, machine learning preparation, or batch transformations, use 'submit_spark_job'. Do not use SQL for high-resource transformations.

3. DATA QUALITY & PROMOTION (Staging Pattern):
   - When generating PySpark transformations, write the output back to a staging table (e.g., 'shipments_agent_staging') instead of writing directly to the production 'shipments' table.
   - Run automated validation rules, and then use SQL to MERGE (Preview) the staging rows into production.

4. TEMPORAL RECONCILIATION:
   - For billing and contract audits, write SQL queries leveraging Iceberg Time Travel: 'FOR SYSTEM_TIME AS OF'. Note that BigQuery queries are limited to a 7-day time travel window.

5. UNSTRUCTURED LATE-STAGE BLENDING:
   - When asked to analyze driver reports or PDF claims associated with structured records, perform a late-stage blend:
     First, write a SQL query to filter the structured Iceberg table to isolate the specific targeted rows. 
     Second, join those rows with the GCS Object Table (via BigQueryObjectRefs).
     Third, apply AI.GENERATE_TEXT to run Gemini only on those filtered rows to analyze the files.
"""

def create_swiftroute_agent() -> Agent:
    """Instantiates the ADK Agent with our system instructions, custom tools, and MCP tools."""
    # Initialize the Vertex AI SDK
    aiplatform.init(
        project=os.getenv("GCP_PROJECT_ID"),
        location=os.getenv("GCP_REGION", "us-central1")
    )
    
    # Retrieve the Knowledge Catalog MCP Toolset (synchronous instantiation)
    catalog_mcp_toolset = get_knowledge_catalog_mcp_toolset()
    
    # Wrap our execution functions explicitly into FunctionTool instances
    sql_tool = FunctionTool(execute_lakehouse_sql)
    spark_tool = FunctionTool(submit_spark_job)
    
    # Combine our custom function tools with our MCP toolset
    all_tools = [sql_tool, spark_tool, catalog_mcp_toolset]
    
    agent = Agent(
        name="swift_route_lakehouse_agent",
        instruction=SYSTEM_INSTRUCTION,
        model="gemini-3.8-flash",  # Leveraging state-of-the-art agentic reasoning
        tools=all_tools
    )
    return agent
