-- Generated from NoSQL JSON (flattened)
DROP TABLE IF EXISTS converted_table;
CREATE TABLE converted_table (
  `customer` TEXT
  `date` TEXT
  `items_0_product` TEXT
  `items_0_qty` TEXT
  `items_1_product` TEXT
  `items_1_qty` TEXT
  `order_id` TEXT);

INSERT INTO converted_table (`customer`, `date`, `items_0_product`, `items_0_qty`, `items_1_product`, `items_1_qty`, `order_id`) VALUES ('Alice', '2025-11-28', 'Laptop', '1', 'Mouse', '2', '1');