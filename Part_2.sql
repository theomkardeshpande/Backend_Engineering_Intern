-- Company owns warehouses and suppliers
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE warehouses (
    id SERIAL PRIMARY KEY,
    company_id INT NOT NULL REFERENCES companies(id),
    name VARCHAR(255) NOT NULL,
    UNIQUE (company_id, name)
);

CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    company_id INT NOT NULL REFERENCES companies(id),
    name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255)
);

-- Products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    price NUMERIC(12, 2) NOT NULL,
    type VARCHAR(50) NOT NULL DEFAULT 'standard'  -- e.g. 'standard' or 'bundle'
);

-- To represent bundles containing other products
CREATE TABLE product_bundles (
    bundle_product_id INT NOT NULL REFERENCES products(id),
    component_product_id INT NOT NULL REFERENCES products(id),
    quantity INT NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (bundle_product_id, component_product_id)
);

-- Inventory per product per warehouse, different quantities
CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(id),
    warehouse_id INT NOT NULL REFERENCES warehouses(id),
    quantity INT NOT NULL CHECK (quantity >= 0),
    UNIQUE (product_id, warehouse_id)
);

-- Track all inventory changes (additions, removals)
CREATE TABLE inventory_changes (
    id SERIAL PRIMARY KEY,
    inventory_id INT NOT NULL REFERENCES inventory(id),
    change INT NOT NULL,           -- positive or negative quantity change
    change_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reason VARCHAR(255)            -- optional description, e.g. sales, restock
);

-- Products supplied by suppliers
CREATE TABLE product_suppliers (
    product_id INT NOT NULL REFERENCES products(id),
    supplier_id INT NOT NULL REFERENCES suppliers(id),
    PRIMARY KEY (product_id, supplier_id)
);

-- Sales activity could be tracked separately (not specified)
CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(id),
    warehouse_id INT NOT NULL REFERENCES warehouses(id),
    quantity INT NOT NULL,
    sale_date TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
