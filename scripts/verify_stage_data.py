from urllib.parse import urlparse
import pandas as pd
import polars as pl
import yaml
from utils import get_s3_client, count_avro_records, lake_env

s3 = get_s3_client()

CFG_PATH = "spark/jobs/stage_tables.yaml"
BUCKET_STAGE = "lakehouse"
PREFIX_STAGE = "stage/storefront/"

storage_options = {
    "aws_access_key_id": lake_env["MINIO_ROOT_USER"],
    "aws_secret_access_key": lake_env["MINIO_ROOT_PASSWORD"],
    "endpoint_url": lake_env["MINIO_ENDPOINT"],
}


def load_cfg():
    with open(CFG_PATH, "r") as f:
        return yaml.safe_load(f)


def scan_stage_table(base: str) -> pl.LazyFrame:
    return pl.scan_parquet(
        f"{base}**/*.parquet",
        storage_options=storage_options,
        low_memory=True,
    )


def parse_raw_bucket_and_prefix(source_path: str):
    parsed = urlparse(source_path.replace("s3a://", "s3://"))
    return parsed.netloc, parsed.path.lstrip("/")


def pl_dtype_to_canonical(dt: pl.DataType) -> str:
    if dt == pl.Int64:
        return "bigint"
    if dt == pl.Int32:
        return "int"
    if dt == pl.Int16:
        return "smallint"
    if dt == pl.Int8:
        return "tinyint"
    if dt == pl.Utf8:
        return "string"
    if dt == pl.Boolean:
        return "boolean"
    if dt == pl.Float32:
        return "float"
    if dt == pl.Float64:
        return "double"
    if dt == pl.Date:
        return "date"
    if isinstance(dt, pl.Decimal):
        return f"decimal({dt.precision},{dt.scale})"
    return str(dt).lower()


def yaml_type_to_canonical(s: str) -> str:
    return s.strip().lower()


cfg = load_cfg()
tables_cfg = cfg["sources"][0]["tables"]
records = []

for t in tables_cfg:
    name = t["name"]
    filter_ops = t.get("filter_op", [])
    source_path = t["source_path"]

    raw_bucket, raw_prefix = parse_raw_bucket_and_prefix(source_path)
    raw_count = count_avro_records(s3, raw_bucket, raw_prefix, filter_ops)

    base = f"s3://{BUCKET_STAGE}/{PREFIX_STAGE}{name}/"
    lf = scan_stage_table(base)
    stage_schema = lf.schema
    stage_count = lf.select(pl.len()).collect().item()

    expected_cols = {c["name"]: yaml_type_to_canonical(c["type"]) for c in t["schema"]}
    missing = [c for c in expected_cols if c not in stage_schema]
    mismatches = [
        f"{c}: expected {expected_cols[c]}, got {pl_dtype_to_canonical(stage_schema[c])}"
        for c in expected_cols
        if c in stage_schema
        and pl_dtype_to_canonical(stage_schema[c]) != expected_cols[c]
    ]
    schema_match = len(missing) == 0 and len(mismatches) == 0

    records.append(
        {
            "table": name,
            "raw_avro_count": raw_count,
            "stage_parquet_count": stage_count,
            "counts_match": raw_count == stage_count,
            "schema_match": schema_match,
            "issues": "; ".join(missing + mismatches),
        }
    )

df = pd.DataFrame(records)
print(df)

if not (df["counts_match"].all() and df["schema_match"].all()):
    raise Exception("Stage verification failed: mismatch detected!")
