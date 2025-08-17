from typing import Iterator, Optional
import boto3
from dotenv import dotenv_values
import psycopg
from smart_open import open as smart_open
import fastavro
import pandas as pd


source_env = dotenv_values(".source.env")
lake_env = dotenv_values(".lake.env")


pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 10_000)
pd.set_option("display.max_colwidth", None)
pd.set_option("display.expand_frame_repr", False)


def get_s3_client() -> boto3.client:
    return boto3.client(
        "s3",
        endpoint_url=lake_env["MINIO_ENDPOINT"],
        aws_access_key_id=lake_env["MINIO_ROOT_USER"],
        aws_secret_access_key=lake_env["MINIO_ROOT_PASSWORD"],
        region_name="us-east-1",
    )


def get_pg_conn() -> psycopg.Connection:
    return psycopg.connect(
        host="localhost",
        port="4444",
        dbname="storefront",
        user=source_env["POSTGRES_USER"],
        password=source_env["POSTGRES_PASSWORD"],
    )


def get_table_row_counts(conn: psycopg.Connection, tables: list[str]) -> dict[str, int]:
    counts = {}
    with conn.cursor() as cur:
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM public.{table}")
            counts[table] = cur.fetchone()[0]
    return counts


def list_s3_objects(
    s3: boto3.client, bucket: str, prefix: str, suffix: Optional[str] = None
) -> Iterator[str]:
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if suffix is None or key.endswith(suffix):
                yield key


def count_avro_records(
    s3: boto3.client, bucket: str, prefix: str, filter_ops: Optional[list[str]] = None
) -> int:
    total = 0
    for key in list_s3_objects(s3, bucket, prefix, suffix=".avro"):
        with smart_open(
            f"s3://{bucket}/{key}", "rb", transport_params={"client": s3}
        ) as fh:
            for rec in fastavro.reader(fh):
                if not filter_ops or rec.get("op") in filter_ops:
                    total += 1
    return total
