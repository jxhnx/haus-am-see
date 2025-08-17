import pandas as pd
from utils import get_s3_client, get_pg_conn, get_table_row_counts, count_avro_records

tables = ["customers", "order_items", "orders", "payments", "products"]
bucket = "raw"
prefix_template = "kafka/storefront.public.{}"

s3 = get_s3_client()
conn = get_pg_conn()
tables_actual_counts = get_table_row_counts(conn, tables)

record_counts = []
for table, expected in tables_actual_counts.items():
    prefix = prefix_template.format(table)
    actual = count_avro_records(s3, bucket, prefix)
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
    raise Exception("One or more tables failed record count match!")
