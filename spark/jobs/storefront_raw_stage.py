from pathlib import Path
from typing import Any, Tuple, List, Dict

import yaml
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.functions import col

from lakehouse.spark_session import get_spark

STAGE_CONFIG = Path(__file__).parent / "stage_tables.yaml"
STAGE_NAMESPACE = "lakehouse.stage.storefront"


def load_config() -> dict[str, Any]:
    with open(STAGE_CONFIG) as f:
        return yaml.safe_load(f)


def _prep_dataframe(
    df: DataFrame, table_cfg: dict[str, Any]
) -> Tuple[DataFrame, List[str], Dict[str, str]]:
    filter_ops = table_cfg.get("filter_op", [])
    schema_map = {c["name"]: c["source"] for c in table_cfg["schema"]}
    type_map = {c["name"]: c["type"] for c in table_cfg["schema"]}

    if filter_ops:
        df = df.filter(col("op").isin(filter_ops))

    for tgt, src in schema_map.items():
        df = df.withColumn(tgt, col(src).cast(type_map[tgt]))

    output_cols = list(schema_map.keys())
    full_type_map = type_map.copy()

    if "created_at" in output_cols:  # use business time stamp
        df = df.withColumn(
            "event_date", F.to_date((F.col("created_at") / 1_000_000).cast("timestamp"))
        )
        df = df.withColumn("event_date_source", F.lit("created_at"))
        output_cols += ["event_date", "event_date_source"]
        full_type_map["event_date"] = "date"
        full_type_map["event_date_source"] = "string"
    elif "ts_ms" in df.columns:  # use Kafka ingest time stamp
        df = df.withColumn(
            "event_date", F.to_date((F.col("ts_ms") / 1000).cast("timestamp"))
        )
        df = df.withColumn("event_date_source", F.lit("ts_ms"))
        output_cols += ["event_date", "event_date_source"]
        full_type_map["event_date"] = "date"
        full_type_map["event_date_source"] = "string"

    return df.select(*output_cols), output_cols, full_type_map


def ingest_table(spark: SparkSession, table_cfg: dict[str, Any]) -> None:
    name = table_cfg["name"]
    source_path = table_cfg["source_path"]
    fmt = table_cfg["format"]
    partitions = table_cfg.get("partitions", [])
    user_props = table_cfg.get("table_properties", {})

    table_fqn = f"{STAGE_NAMESPACE}.{name}"
    print(f"Ingesting '{name}' from {source_path}")

    raw = spark.read.format(fmt).load(source_path)
    df_final, output_cols, type_map = _prep_dataframe(raw, table_cfg)

    if df_final.limit(1).count() == 0:
        print(f"No rows to write for {table_fqn}")
        return

    spark.sql(f"CREATE NAMESPACE IF NOT EXISTS {STAGE_NAMESPACE}")

    default_props = {
        "format-version": "2",
        "write.parquet.compression-codec": "snappy",
    }
    table_props = {**default_props, **user_props}

    exists = spark._jsparkSession.catalog().tableExists(table_fqn)

    if not exists:
        writer = df_final.writeTo(table_fqn)
        if partitions:
            writer = writer.partitionedBy(*[col(p) for p in partitions])
        for k, v in table_props.items():
            writer = writer.tableProperty(str(k), str(v))
        writer.create()
        print(f"Created table {table_fqn}")
    else:
        df_final.writeTo(table_fqn).append()
        print(f"Appended to {table_fqn}")


def main() -> None:
    spark = get_spark("bronze_ingest_job")
    config = load_config()
    for table in config["sources"][0]["tables"]:
        ingest_table(spark, table)


if __name__ == "__main__":
    main()
