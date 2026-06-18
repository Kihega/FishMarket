-- SmartFish – Fish Market Access & Distribution System
-- Reference schema v2 (run via Laravel migrations on PlanetScale)

CREATE TABLE users (
  id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name                VARCHAR(255) NOT NULL,
  email               VARCHAR(255) NOT NULL UNIQUE,
  password            VARCHAR(255) NOT NULL,
  role                ENUM('admin','seller','buyer') DEFAULT 'buyer',
  phone               VARCHAR(50),
  location            VARCHAR(255),
  brand_logo          VARCHAR(255),
  office_address      VARCHAR(255),
  location_address    VARCHAR(255),
  bio                 TEXT,
  is_active           TINYINT(1) DEFAULT 1,
  subscription_status ENUM('active','pending','inactive') DEFAULT 'inactive',
  created_at TIMESTAMP NULL, updated_at TIMESTAMP NULL
);

CREATE TABLE fish_categories (
  id   BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL UNIQUE,
  description VARCHAR(255),
  created_at TIMESTAMP NULL, updated_at TIMESTAMP NULL
);

CREATE TABLE fish_stocks (
  id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  seller_id    BIGINT UNSIGNED NOT NULL,
  category_id  BIGINT UNSIGNED NOT NULL,
  fish_name    VARCHAR(255) NOT NULL,
  image        VARCHAR(255),
  quantity_kg  DECIMAL(10,2) DEFAULT 0,
  price_per_kg DECIMAL(10,2) NOT NULL,
  status       ENUM('active','out_of_stock') DEFAULT 'active',
  created_at TIMESTAMP NULL, updated_at TIMESTAMP NULL,
  FOREIGN KEY (seller_id)   REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (category_id) REFERENCES fish_categories(id)
);

CREATE TABLE delivery_agencies (
  id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  seller_id    BIGINT UNSIGNED NOT NULL,
  agency_name  VARCHAR(255) NOT NULL,
  contact      VARCHAR(100),
  area_covered VARCHAR(255),
  is_active    TINYINT(1) DEFAULT 1,
  created_at TIMESTAMP NULL, updated_at TIMESTAMP NULL,
  FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE orders (
  id             BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  buyer_id       BIGINT UNSIGNED NOT NULL,
  seller_id      BIGINT UNSIGNED NOT NULL,
  status         ENUM('pending','received','confirmed','processed','cancelled') DEFAULT 'pending',
  payment_method ENUM('mobile','bank'),
  payment_status ENUM('unpaid','paid') DEFAULT 'unpaid',
  total_amount   DECIMAL(12,2) DEFAULT 0,
  created_at TIMESTAMP NULL, updated_at TIMESTAMP NULL,
  FOREIGN KEY (buyer_id)  REFERENCES users(id),
  FOREIGN KEY (seller_id) REFERENCES users(id)
);

CREATE TABLE order_items (
  id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  order_id     BIGINT UNSIGNED NOT NULL,
  stock_id     BIGINT UNSIGNED NOT NULL,
  fish_name    VARCHAR(255) NOT NULL,
  quantity_kg  DECIMAL(10,2),
  price_per_kg DECIMAL(10,2),
  subtotal     DECIMAL(12,2),
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  FOREIGN KEY (stock_id) REFERENCES fish_stocks(id)
);

CREATE TABLE order_deliveries (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  order_id        BIGINT UNSIGNED NOT NULL,
  agency_id       BIGINT UNSIGNED NOT NULL,
  delivery_method VARCHAR(100),
  delivery_status ENUM('pending','dispatched','delivered') DEFAULT 'pending',
  created_at TIMESTAMP NULL, updated_at TIMESTAMP NULL,
  FOREIGN KEY (order_id)  REFERENCES orders(id) ON DELETE CASCADE,
  FOREIGN KEY (agency_id) REFERENCES delivery_agencies(id)
);

CREATE TABLE bills (
  id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  order_id    BIGINT UNSIGNED NOT NULL UNIQUE,
  buyer_id    BIGINT UNSIGNED NOT NULL,
  bill_number VARCHAR(50) UNIQUE,
  issued_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMP NULL, updated_at TIMESTAMP NULL,
  FOREIGN KEY (order_id) REFERENCES orders(id),
  FOREIGN KEY (buyer_id) REFERENCES users(id)
);

CREATE TABLE subscriptions (
  id        BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  seller_id BIGINT UNSIGNED NOT NULL,
  plan      ENUM('monthly','annual'),
  amount    DECIMAL(10,2),
  status    ENUM('pending','active','expired') DEFAULT 'pending',
  paid_at   TIMESTAMP NULL,
  created_at TIMESTAMP NULL, updated_at TIMESTAMP NULL,
  FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE
);
