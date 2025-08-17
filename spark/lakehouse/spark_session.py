import os
from pyspark.sql import SparkSession


def get_spark(app_name: str = "LakehouseJob") -> SparkSession:
    return (
        SparkSession.builder.appName(app_name)
        .master(os.environ["SPARK_MASTER_URL"])
        # Iceberg HadoopCatalog config
        .config("spark.sql.catalog.lakehouse", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.lakehouse.type", "hadoop")
        .config(
            "spark.sql.catalog.lakehouse.warehouse",
            os.environ["SPARK_SQL_CATALOG_LAKEHOUSE_WAREHOUSE"],
        )
        # MinIO / S3A config
        .config(
            "spark.hadoop.fs.s3a.endpoint", os.environ["SPARK_HADOOP_FS_S3A_ENDPOINT"]
        )
        .config(
            "spark.hadoop.fs.s3a.access.key",
            os.environ["SPARK_HADOOP_FS_S3A_ACCESS_KEY"],
        )
        .config(
            "spark.hadoop.fs.s3a.secret.key",
            os.environ["SPARK_HADOOP_FS_S3A_SECRET_KEY"],
        )
        .config(
            "spark.hadoop.fs.s3a.path.style.access",
            os.environ["SPARK_HADOOP_FS_S3A_PATH_STYLE_ACCESS"],
        )
        .config("spark.hadoop.fs.s3a.impl", os.environ["SPARK_HADOOP_FS_S3A_IMPL"])
        # Iceberg Spark extensions
        .config(
            "spark.sql.extensions",
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
        )
        .getOrCreate()
    )
