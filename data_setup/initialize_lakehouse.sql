-- data_setup/initialize_lakehouse.sql

-- 1. Create the SwiftRoute Lakehouse Dataset
CREATE SCHEMA IF NOT EXISTS `swiftroute_lakehouse`
OPTIONS(
  location="us-central1"
);

-- 2. Initialize the Structured Shipments Telemetry Table (Mocked as Iceberg)
-- Note: Under Google Cloud Lakehouse, Iceberg tables are managed via the Lakehouse Runtime Catalog.
-- For local testing, we initialize this as a standard table with Iceberg configurations.
CREATE OR REPLACE TABLE `swiftroute_lakehouse.shipments`
(
  shipment_id STRING OPTIONS(description="Unique shipping transaction ID prefixed with TRX-"),
  customer_id STRING OPTIONS(description="The unique customer account identifier"),
  dispatch_time TIMESTAMP OPTIONS(description="The UTC timestamp when the shipment left the depot"),
  shipping_cost NUMERIC OPTIONS(description="The total baseline cost of the shipment in USD"),
  destination_country STRING OPTIONS(description="The destination country name, frequently recorded in dirty/un-normalized formats"),
  status STRING OPTIONS(description="The current transaction delivery status: DELIVERED, DISPUTED, or DAMAGED")
)
AS
SELECT 
  CONCAT('TRX-', CAST(id AS STRING)) as shipment_id,
  CAST(id AS STRING) as customer_id,
  TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL CAST(RAND() * 10000 AS INT64) MINUTE) as dispatch_time,
  CAST(100 + RAND() * 5000 AS NUMERIC) as shipping_cost,
  -- Intentionally dirty country codes for our Spark agent to clean
  CASE 
    WHEN RAND() < 0.25 THEN 'FR'
    WHEN RAND() < 0.50 THEN 'France'
    WHEN RAND() < 0.75 THEN 'fr'
    ELSE 'FR-fr'
  END as destination_country,
  CASE 
    WHEN RAND() < 0.1 THEN 'DAMAGED'
    WHEN RAND() < 0.15 THEN 'DISPUTED'
    ELSE 'DELIVERED'
  END as status
FROM UNNEST(GENERATE_ARRAY(1, 1000)) as id;

-- 3. Initialize the Unstructured Delivery Claims (Mocking GCS Object Table references)
CREATE OR REPLACE TABLE `swiftroute_lakehouse.unstructured_claims`
(
  shipment_id STRING OPTIONS(description="The target shipment ID matching the shipments table"),
  customer_id INT64 OPTIONS(description="The customer ID associated with the claim"),
  object_uri STRING OPTIONS(description="The GCS ObjectRef URI pointing to the driver claim PDF"),
  driver_notes STRING OPTIONS(description="Raw text notes written on-site by the delivery driver")
)
AS
SELECT 
  CONCAT('TRX-', CAST(id AS STRING)) as shipment_id,
  id as customer_id,
  CONCAT('gs://swiftroute-claims-bucket/claim_', CAST(id AS STRING), '.pdf') as object_uri,
  CONCAT('Driver Report: Package was damaged during transit due to excessive cargo shifting. Item ID ', CAST(id AS STRING)) as driver_notes
FROM UNNEST(GENERATE_ARRAY(1, 1000)) as id
WHERE MOD(id, 10) = 0; -- Simulates claims for damaged or disputed subset
