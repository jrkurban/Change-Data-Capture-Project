from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType, IntegerType, ArrayType
from pyspark.sql.functions import expr, from_json, col, concat
from pyspark.sql import SparkSession, functions as F
from pyspark import SparkContext

spark = SparkSession.builder.appName("abc") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.1") \
    .getOrCreate()
spark.sparkContext.setLogLevel("DEBUG")

accessKeyId = 'dataops'
secretAccessKey = 'Ankara06'

# Define the schema for the JSON data
schema = StructType([
    StructField("payload", StructType([
        StructField("before", StructType([
            StructField("customerId", IntegerType()),
            StructField("customerFName", StringType()),
            StructField("customerLName", StringType()),
            StructField("customerEmail", StringType()),
            StructField("customerPassword", StringType()),
            StructField("customerStreet", StringType()),
            StructField("customerCity", StringType()),
            StructField("customerState", StringType()),
            StructField("customerZipcode", IntegerType())
        ])),
        StructField("after", StructType([
            StructField("customerId", IntegerType()),
            StructField("customerFName", StringType()),
            StructField("customerLName", StringType()),
            StructField("customerEmail", StringType()),
            StructField("customerPassword", StringType()),
            StructField("customerStreet", StringType()),
            StructField("customerCity", StringType()),
            StructField("customerState", StringType()),
            StructField("customerZipcode", IntegerType())
        ])),
        StructField("ts_ms", StringType()),
        StructField("op", StringType())
    ]))
])

# Read messages from Kafka
kafka_df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "dbserver1.public.customers") \
    .load() \
    .select(from_json(col("value").cast("string"), schema).alias("data")) \
    .select("data.payload.*")

# Print the schema
kafka_df.printSchema()


# Parse JSON data
#json_df = kafka_df.select(from_json(col("value").cast("string"), schema).alias("value"))



def load_config(spark_context: SparkContext):
    spark_context._jsc.hadoopConfiguration().set('fs.s3a.access.key', accessKeyId)
    spark_context._jsc.hadoopConfiguration().set('fs.s3a.secret.key', secretAccessKey)
    spark_context._jsc.hadoopConfiguration().set('fs.s3a.path.style.access', 'true')
    spark_context._jsc.hadoopConfiguration().set('fs.s3a.impl', 'org.apache.hadoop.fs.s3a.S3AFileSystem')
    spark_context._jsc.hadoopConfiguration().set('fs.s3a.endpoint', 'http://minio:9000')


checkpointDir = "file:///tmp/streaming/writefrom_kafka"
load_config(spark.sparkContext)
py_stream= kafka_df.writeStream \
    .format("json") \
    .option("path", "s3a://datasets/customers/customer.json") \
    .option("checkpointLocation", checkpointDir) \
    .start()
py_stream.awaitTermination()