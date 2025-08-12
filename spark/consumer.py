from pyspark.sql import SparkSession
from pyspark.sql.functions import col, regexp_extract, to_timestamp

# Function to write each micro-batch to PostgreSQL
def write_to_postgres(batch_df, batch_id):
    batch_df.select("ip", "timestamp", "method", "endpoint", "protocol", "status", "size") \
        .write \
        .format("jdbc") \
        .option("url", "jdbc:postgresql://host.docker.internal:5432/log_db") \
        .option("dbtable", "parsed_logs") \
        .option("user", "postgres") \
        .option("password", "011145") \
        .option("driver", "org.postgresql.Driver") \
        .mode("append") \
        .save()

# Create SparkSession
spark = SparkSession.builder \
    .appName("KafkaLogConsumer") \
    .master("spark://spark-master:7077") \
    .getOrCreate()

# Read from Kafka
df_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "logs") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

# Extract raw log string
logs_df = df_raw.selectExpr("CAST(value AS STRING) as raw_log")

# Write raw logs to HDFS (Bronze Layer)
logs_df.writeStream \
    .format("text") \
    .option("path", "hdfs://namenode:8020/data/bronze/logs/") \
    .option("checkpointLocation", "/tmp/bronze_checkpoint/") \
    .outputMode("append") \
    .start()

# Parse raw logs into structured fields (Silver Layer)
parsed_df = logs_df \
    .withColumn("ip", regexp_extract("raw_log", r"^(\S+)", 1)) \
    .withColumn("timestamp_str", regexp_extract("raw_log", r"\[(.*?)\]", 1)) \
    .withColumn("method", regexp_extract("raw_log", r"\"(\S+)\s", 1)) \
    .withColumn("endpoint", regexp_extract("raw_log", r"\"\S+\s(\S+)\s", 1)) \
    .withColumn("protocol", regexp_extract("raw_log", r"(HTTP/\d\.\d)", 1)) \
    .withColumn("status", regexp_extract("raw_log", r"\"\s(\d{3})\s", 1).cast("int")) \
    .withColumn("size", regexp_extract("raw_log", r"\"\s\d{3}\s(\d+)\s", 1).cast("long")) \
    .withColumn("timestamp", to_timestamp("timestamp_str", "dd/MMM/yyyy:HH:mm:ss Z")) \
    .drop("timestamp_str")

# Write parsed data to PostgreSQL (Gold Layer)
parsed_df.writeStream \
    .foreachBatch(write_to_postgres) \
    .outputMode("append") \
    .option("checkpointLocation", "/tmp/postgres_checkpoint/") \
    .start() \
    .awaitTermination()
