-- Drop tables if they exist to ensure a clean slate
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;

-- Create Customers Table
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100) UNIQUE,
    country VARCHAR(50),
    registration_date DATE
);

-- Create Orders Table
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    order_date TIMESTAMP,
    total_amount NUMERIC(10, 2)
);

-- Insert Sample Data into Customers
INSERT INTO customers (first_name, last_name, email, country, registration_date) VALUES
('John', 'Smith', 'john.smith@example.com', 'USA', '2024-01-15'),
('Jane', 'Doe', 'jane.doe@example.com', 'Canada', '2024-02-20'),
('Peter', 'Jones', 'peter.jones@example.com', 'UK', '2024-03-10'),
('Mei', 'Lin', 'mei.lin@example.com', 'USA', '2024-04-05'),
('Saanvi', 'Gupta', 'saanvi.gupta@example.com', 'India', '2025-07-12');

-- Insert Sample Data into Orders
-- Note: The prompt specifically mentions July 2025
INSERT INTO orders (customer_id, order_date, total_amount) VALUES
(1, '2025-07-01 10:00:00', 150.50),
(2, '2025-07-02 11:30:00', 75.00),
(1, '2025-07-05 14:00:00', 200.00),
(3, '2025-07-10 09:00:00', 350.75),
(4, '2025-07-15 16:45:00', 50.25),
(5, '2025-07-18 18:00:00', 999.99),
(2, '2025-07-20 12:00:00', 120.00),
(1, '2025-08-01 10:00:00', 300.00); -- An order outside July for testing filters

-- Add a key for Redis seeding
-- This part is just for reference, Redis keys are set via client commands
-- SET user:session:123 '{"username":"john.smith","role":"viewer"}'
-- SET system:config '{"maintenance_mode": "false"}'
