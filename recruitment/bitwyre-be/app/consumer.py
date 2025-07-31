# from redpanda import RedPandaConsumer
import json
from kafka import KafkaConsumer
import mysql.connector

# Redpanda configuration
consumer = KafkaConsumer(
    bootstrap_servers=["localhost:9092"],
    group_id="demo-group",
    auto_offset_reset="earliest",
    enable_auto_commit=False,
    consumer_timeout_ms=1000,
    value_deserializer=lambda m: json.loads(m.decode("ascii")),
)
consumer.subscribe("crypto_transaction")

# MariaDB configuration
mariadb_config = {
    "host": "localhost",
    "port": "3306",
    "user": "bitwyre",
    "password": "example",
    "database": "crypto_transaction",
}

# Set up MariaDB connection
mariadb_connection = mysql.connector.connect(**mariadb_config, autocommit=True)
mariadb_cursor = mariadb_connection.cursor()


def save_to_mariadb(data):
    # Assuming the data has fields: timestamp, price, volume
    sql = "INSERT INTO crypto_transaction (id, timestamp, price, volume) VALUES (%s, %s, %s, %s)"
    val = (data["id"], data["timestamp"], data["price"], data["volume"])
    mariadb_cursor.execute(sql, val)


def consume_data():
    for message in consumer:
        topic_info = f"topic: {message.partition}|{message.offset})"
        message_info = f"key: {message.key}, {message.value}"
        message.value["id"] = message.offset
        # print(f"{topic_info}, {message_info}")
        print(message.value)
        save_to_mariadb(message.value)


if __name__ == "__main__":
    consume_data()
