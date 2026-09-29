# SwiftRoute Agentic Lakehouse Pipeline

A production-grade, secure, multi-engine agentic AI blueprint designed to orchestrate SQL, PySpark, and unstructured GCS Object Table operations directly over Apache Iceberg tables in Google Cloud Lakehouse.

This repository demonstrates how to build an intelligent, autonomous Data Agent using **ADK 2.0** and **Gemini 3.8 Flash** that dynamically decides whether to run a fast SQL query or spin up a serverless Spark job based on business intent and data scale.

---

## Repository Structure

```text
swiftroute-agentic-lakehouse/
├── README.md
├── requirements.txt
├── terraform/
│   ├── main.tf              # Provisions IAM SA, REST Catalog, and Taxonomies
│   ├── variables.tf
│   └── outputs.tf
├── data_setup/
│   └── initialize_lakehouse.sql  # SQL schema and mock telemetry data generator
└── agent/
    ├── __init__.py
    ├── agent.py             # Core ADK 2.0 agent and multi-engine tool definitions
    └── main.py              # Automated, three-pillar sequential demo driver

```

Technical Architecture Overview
-------------------------------

The system is cleanly divided into a secure, governing **Control Plane** and a high-performance **Data Plane**:

*   **Control Plane (Gemini Enterprise Agent Platform):** Handles agent orchestration, SPIFFE-based attested Workload Identities, and routes user traffic through the **Agent Gateway** to enforce **Model Armor** policies and **Semantic Governance**.
    
*   **Data Plane (Google Cloud Lakehouse):** Utilizes **Apache Iceberg** open storage formats managed by the **Lakehouse Runtime Catalog (REST)**, and the **Knowledge Catalog** (lookup\_context API) for semantic asset discovery.

---

Quick Start: Local Dry-Run Mode (30 Seconds)
--------------------------------------------

To test the entire agentic loop, tool-routing logic, and code generation locally **completely for free with zero GCP infrastructure setup**, run the repository in Dry-Run Mode:

### 1\. Clone the Repository

```text
git clone https://github.com/your-username/swiftroute-agentic-lakehouse.git

cd swiftroute-agentic-lakehouse
```

### 2\. Install Dependencies

```text
pip install -r requirements.txt
pip install google-adk[mcp]
```

### 3\. Export Your Gemini API Key

Generate a free API Key in [Google AI Studio](https://www.google.com/url?q=https://www.google.com/url?q=https%3A%2F%2Faistudio.google.com%2F) and export it in your terminal:

```text
export GOOGLE\_API\_KEY="AIzaSyYourActualKeyHere"
```

4\. Run the Automated Demo Suite

```text
python agent/main.py
```

Production Setup: Running "For Real" on Google Cloud
----------------------------------------------------

When you are ready to transition from simulation to physical, live execution over GCP data infrastructure, follow this deployment playbook:

### 1\. Enable Required Google Cloud APIs

Ensure your terminal is authenticated to your GCP project:

```text
gcloud services enable \
  aiplatform.googleapis.com \
  bigquery.googleapis.com \
  dataplex.googleapis.com \
  datacatalog.googleapis.com \
  dataproc.googleapis.com \
  run.googleapis.com
```

### 2\. Initialize the Database Dataset

1.  Copy the contents of /data\_setup/initialize\_lakehouse.sql.
    
2.  Open the [Google Cloud Console BigQuery Editor](https://console.cloud.google.com/?chat=true&authuser=1&project=dssetup-202519) .
    
3.  Paste the script and click **Run**. This provisions the dataset, generates 1,000 rows of dirty shipping data, and populates the Knowledge Catalog metadata.

### 3\. Provision Infrastructure via Terraform

Navigate to the /terraform folder and apply the IaC configuration:

```text
cd terraform
terraform init
terraform apply \
  -var="project_id=<YOUR_GCP_PROJECT_ID>" \
  -var="spark_jobs_bucket=<YOUR_GCS_SPARK_BUCKET_NAME>"

```

### 4\. Authenticate Application Default Credentials (ADC)

Authorize your local session to make physical API calls to your GCP project:

```text
gcloud auth application-default login
```

### 5\. Disable Dry-Run Mode and Execute

Export the active environment variables to target your physical GCP resources, setting LAKEHOUSE\_DRY\_RUN to false:

```text
export LAKEHOUSE\_DRY\_RUN="false"export GCP\_PROJECT\_ID=""
export GCP\_REGION="us-central1"
export GCP\_SPARK\_BUCKET=""

# Run the physical execution pipeline
python agent/main.py
```

Verifying the Physical Execution
--------------------------------

After running the physical pipeline, you can verify the results directly inside BigQuery:

1.  **GCS Script Verification:** Verify that the agent successfully generated and uploaded the PySpark script to gs:///temp\_agent\_job.py.
    
2.  **Dataproc Batch Verification:** Open the Dataproc Serverless console to see the active or completed Spark batch execution.
    
3.  **Data Quality Audit:** Once the Spark job completes, run this query in BigQuery to verify that the dirty country codes have been successfully normalized into the staging table:

```text
  
SELECT DISTINCT destination\_country FROM \`your\_project\_id.swiftroute\_lakehouse.shipments\_agent\_staging\`;

-- Expected Output: Only 'FR' and clean ISO codes should remain.

```
