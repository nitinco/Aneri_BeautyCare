-- SQL CREATE TABLE statements for missing modules
-- Billing & Payment
CREATE TABLE IF NOT EXISTS `bill` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `customer_id` INT NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `total_amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `tax_amount` DECIMAL(10,2) DEFAULT 0.00,
  `discount_amount` DECIMAL(10,2) DEFAULT 0.00,
  `status` VARCHAR(50) DEFAULT 'unpaid',
  FOREIGN KEY (`customer_id`) REFERENCES `customer` (`id`) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS `bill_detail` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `bill_id` INT NOT NULL,
  `service_id` INT DEFAULT NULL,
  `product_id` INT DEFAULT NULL,
  `description` VARCHAR(255),
  `quantity` INT DEFAULT 1,
  `unit_price` DECIMAL(10,2) DEFAULT 0.00,
  `amount` DECIMAL(10,2) DEFAULT 0.00,
  FOREIGN KEY (`bill_id`) REFERENCES `bill`(`id`) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS `payment` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `bill_id` INT NOT NULL,
  `amount` DECIMAL(10,2) NOT NULL,
  `method` VARCHAR(50),
  `provider` VARCHAR(50),
  `provider_payment_id` VARCHAR(255),
  `status` VARCHAR(50) DEFAULT 'pending',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`bill_id`) REFERENCES `bill`(`id`) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS `charge` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `payment_id` INT NOT NULL,
  `type` VARCHAR(50),
  `amount` DECIMAL(10,2) DEFAULT 0.00,
  `description` VARCHAR(255),
  FOREIGN KEY (`payment_id`) REFERENCES `payment`(`id`) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS `charge_detail` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `charge_id` INT NOT NULL,
  `key_name` VARCHAR(100),
  `key_value` VARCHAR(255),
  FOREIGN KEY (`charge_id`) REFERENCES `charge`(`id`) ON DELETE CASCADE
);

-- Product & Inventory
CREATE TABLE IF NOT EXISTS `brand` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(120) NOT NULL,
  `description` VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS `product` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(200) NOT NULL,
  `brand_id` INT,
  `sku` VARCHAR(120),
  `price` DECIMAL(10,2) DEFAULT 0.00,
  `is_active` BOOLEAN DEFAULT TRUE,
  FOREIGN KEY (`brand_id`) REFERENCES `brand`(`id`) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS `product_detail` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `product_id` INT NOT NULL,
  `key_name` VARCHAR(100),
  `key_value` VARCHAR(255),
  FOREIGN KEY (`product_id`) REFERENCES `product`(`id`) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS `supplier` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(150) NOT NULL,
  `contact` VARCHAR(120),
  `address` VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS `stock` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `product_id` INT NOT NULL,
  `supplier_id` INT,
  `quantity` INT DEFAULT 0,
  `reorder_level` INT DEFAULT 5,
  `last_updated` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`product_id`) REFERENCES `product`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`supplier_id`) REFERENCES `supplier`(`id`) ON DELETE SET NULL
);

-- Cart & Order
CREATE TABLE IF NOT EXISTS `cart` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `customer_id` INT NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`customer_id`) REFERENCES `customer`(`id`) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS `order_tbl` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `customer_id` INT NOT NULL,
  `cart_id` INT,
  `total_amount` DECIMAL(10,2) DEFAULT 0.00,
  `status` VARCHAR(50) DEFAULT 'pending',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`customer_id`) REFERENCES `customer`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`cart_id`) REFERENCES `cart`(`id`) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS `order_item` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `order_id` INT NOT NULL,
  `product_id` INT NOT NULL,
  `quantity` INT DEFAULT 1,
  `unit_price` DECIMAL(10,2) DEFAULT 0.00,
  FOREIGN KEY (`order_id`) REFERENCES `order_tbl`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`product_id`) REFERENCES `product`(`id`) ON DELETE SET NULL
);

-- Delivery
CREATE TABLE IF NOT EXISTS `delivery` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `order_id` INT NOT NULL,
  `delivery_staff_id` INT,
  `status` VARCHAR(50) DEFAULT 'pending',
  `assigned_at` DATETIME,
  `delivered_at` DATETIME,
  FOREIGN KEY (`order_id`) REFERENCES `order_tbl`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`delivery_staff_id`) REFERENCES `staff`(`id`) ON DELETE SET NULL
);

-- Offers
CREATE TABLE IF NOT EXISTS `offer` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `title` VARCHAR(200) NOT NULL,
  `description` VARCHAR(255),
  `is_product_offer` BOOLEAN DEFAULT FALSE,
  `product_id` INT,
  `service_id` INT,
  `discount_percent` INT DEFAULT 0,
  `start_date` DATE,
  `end_date` DATE,
  `is_active` BOOLEAN DEFAULT TRUE,
  FOREIGN KEY (`product_id`) REFERENCES `product`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`service_id`) REFERENCES `service`(`id`) ON DELETE SET NULL
);

-- Complaint & Feedback
CREATE TABLE IF NOT EXISTS `complaint` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `customer_id` INT NOT NULL,
  `subject` VARCHAR(200),
  `message` TEXT,
  `status` VARCHAR(50) DEFAULT 'open',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `reviewed_by` INT,
  FOREIGN KEY (`customer_id`) REFERENCES `customer`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`reviewed_by`) REFERENCES `users`(`id`) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS `feedback` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `customer_id` INT NOT NULL,
  `rating` INT DEFAULT 5,
  `message` TEXT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`customer_id`) REFERENCES `customer`(`id`) ON DELETE CASCADE
);

-- End of script
