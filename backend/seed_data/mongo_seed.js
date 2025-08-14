// This script is intended to be run via `mongosh`
// e.g., `docker exec -i <container> mongosh -u admin -p password < mongo_seed.js`

// Switch to the main database
db = db.getSiblingDB('maindb');

// Drop existing collections for a clean seed
db.products.drop();
db.reviews.drop();

// Insert sample products
db.products.insertMany([
  {
    "product_id": "P001",
    "name": "Quantum Laptop",
    "category": "Electronics",
    "price": 1200.00,
    "stock": 50,
    "tags": ["laptop", "powerful", "16GB RAM"],
    "added_date": ISODate("2024-05-10T00:00:00Z")
  },
  {
    "product_id": "P002",
    "name": "Acoustic Wireless Headphones",
    "category": "Electronics",
    "price": 250.50,
    "stock": 120,
    "tags": ["audio", "bluetooth", "noise-cancelling"],
    "added_date": ISODate("2024-06-15T00:00:00Z")
  },
  {
    "product_id": "P003",
    "name": "Ergo-Mechanical Keyboard",
    "category": "Peripherals",
    "price": 150.75,
    "stock": 80,
    "tags": ["keyboard", "mechanical", "ergonomic"],
    "added_date": ISODate("2024-07-20T00:00:00Z")
  },
  {
    "product_id": "P004",
    "name": "4K Ultra-HD Monitor",
    "category": "Peripherals",
    "price": 650.00,
    "stock": 40,
    "tags": ["monitor", "4K", "gaming"],
    "added_date": ISODate("2025-07-25T00:00:00Z")
  }
]);

// Insert sample reviews
db.reviews.insertMany([
  {
    "review_id": "R001",
    "product_id": "P001",
    "username": "jane.doe",
    "rating": 5,
    "comment": "Incredibly fast and lightweight!",
    "review_date": ISODate("2025-07-01T00:00:00Z")
  },
  {
    "review_id": "R002",
    "product_id": "P004",
    "username": "john.smith",
    "rating": 4,
    "comment": "Great colors, but the stand is a bit wobbly.",
    "review_date": ISODate("2025-07-30T00:00:00Z")
  },
  {
    "review_id": "R003",
    "product_id": "P002",
    "username": "peter.jones",
    "rating": 5,
    "comment": "Amazing sound quality and battery life.",
    "review_date": ISODate("2025-08-02T00:00:00Z")
  }
]);

print("MongoDB seeded successfully with products and reviews.");