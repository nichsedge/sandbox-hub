CREATE TABLE crypto_transaction (
  id INT AUTO_INCREMENT PRIMARY KEY,
  timestamp DATETIME NOT NULL,
  price DECIMAL(10, 2) NOT NULL,
  volume DECIMAL(10, 2) NOT NULL
);
