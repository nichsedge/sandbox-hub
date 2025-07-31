# Bitwyre - Backend Engineer

## Description

This project provides a Flask-based web application for managing crypto transactions. It consists of two Python scripts that utilize the Flask library to implement endpoints for sending and retrieving crypto transaction data.

The project uses Redpanda, a Kafka-compatible message streaming platform, to handle the data stream from the POST endpoint. The transaction data is then stored in a MariaDB database, which can be accessed through the GET endpoint.

## Installation

1. Clone the repository:
   ```shell
   git clone https://github.com/ichsanulamal/bitwyre-task.git
   ```

2. Activate environment and install the required dependencies:
   ```shell
   cd app
   pip install -r requirements.txt
   ```

3. Start the Redpanda and MariaDB services using Docker Compose:
   ```shell
   docker-compose up -d
   ```

4. Create a Topic 
   ```shell
   docker exec -it redpanda-1 rpk topic create crypto_transaction
   ```

5. Run the application:
   
   - Producer
   ```shell
   python flask_app.py
   ```
   - Consumer
    ```shell
   python consumer.py
   ```

6. The Flask application will be accessible at `http://localhost:5000`.

## Usage

- Send Crypto Transaction Data (POST Endpoint):
  - Endpoint: `/send_data`
  - Method: POST
  - Request Body: JSON data with the following fields:
    - `timestamp` (string): The timestamp of the transaction (format: "YYYY-MM-DDTHH:MM:SS").
    - `price` (float): The price of the transaction.
    - `volume` (float): The volume of the transaction.

- Consume Transaction Data:
  - `python consumer.py`

- Retrieve Crypto Transaction Data (GET Endpoint):
  - Endpoint: `/retrieve_data`
  - Method: GET
  - Response: JSON data with the retrieved crypto transaction data.

## Configuration

- Redpanda Configuration:
  - Redpanda brokers: Update the `redpanda_brokers` variable in `consumer.py` to specify the Redpanda broker(s) to connect to.

- MariaDB Configuration:
  - Database credentials: Update the `user`, `password`, `host`, and `database` variables in `database.py` to match your MariaDB configuration.

- Testing using Postman:
  - Import postman json from `Bitwyre test.postman_collection.json`
  
## Credits

ChatGPT and any docs I got from Googling