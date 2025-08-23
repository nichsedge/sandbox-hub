from flask import Flask, request
import mysql.connector

# from redpanda import RedPandaProducer
import json
from kafka import KafkaProducer
from kafka.errors import KafkaError

app = Flask(__name__)

# Set up Redpanda producer
producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda m: json.dumps(m).encode("ascii"),
)
topic = "crypto_transaction"


def on_success(metadata):
    print(f"Message produced to topic '{metadata.topic}' at offset {metadata.offset}")


def on_error(e):
    print(f"Error sending message: {e}")


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


@app.route("/send_data", methods=["POST"])
def send_data():
    data = request.get_json()
    future = producer.send(topic, data)
    future.add_callback(on_success)
    future.add_errback(on_error)
    return "Data sent to Redpanda topic"


@app.route("/retrieve_data", methods=["GET"])
def retrieve_data():
    mariadb_cursor.execute("SELECT * FROM crypto_transaction")
    result = mariadb_cursor.fetchall()
    data = []
    print(result)
    for row in result:
        data.append({"timestamp": row[1], "price": row[2], "volume": row[3]})
    return {"data": data}


if __name__ == "__main__":
    app.run()
