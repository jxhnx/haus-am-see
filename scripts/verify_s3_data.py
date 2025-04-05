import boto3
import fastavro
from smart_open import open as smart_open
from dotenv import dotenv_values
import pandas as pd
import psycopg

source_env = dotenv_values(".source.env")
lake_env = dotenv_values(".lake.env")

s3 = boto3.client(
    "s3",
    endpoint_url=lake_env["MINIO_ENDPOINT"],
    aws_access_key_id=lake_env["MINIO_ROOT_USER"],
    aws_secret_access_key=lake_env["MINIO_ROOT_PASSWORD"],
    region_name="us-east-1",
)

conn = psycopg.connect(
    host="localhost",
    port="4444",
    dbname="storefront",
    user=source_env["POSTGRES_USER"],
    password=source_env["POSTGRES_PASSWORD"],
)

tables = ["customers", "order_items", "orders", "payments", "products"]
bucket = "raw"
prefix_template = "kafka/storefront.public.{}"

tables_actual_counts = {}
with conn.cursor() as cur:
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM public.{table}")
        count = cur.fetchone()[0]
        tables_actual_counts[table] = count


def count_avro_records(bucket: str, prefix: str) -> int:
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    files = [
        obj["Key"]
        for obj in response.get("Contents", [])
        if obj["Key"].endswith(".avro")
    ]
    total_records = 0
    for file_key in files:
        with smart_open(
            f"s3://{bucket}/{file_key}", "rb", transport_params={"client": s3}
        ) as f:
            reader = fastavro.reader(f)
            total_records += sum(1 for _ in reader)
    return total_records


record_counts = []
for table, expected in tables_actual_counts.items():
    prefix = prefix_template.format(table)
    actual = count_avro_records(bucket, prefix)
    record_counts.append(
        {
            "table": table,
            "postgres_count": expected,
            "s3_count": actual,
            "match": expected == actual,
        }
    )

df_counts = pd.DataFrame(record_counts)
print(df_counts)

if not df_counts["match"].all():
    raise Exception("❌ One or more tables failed record count match!")
