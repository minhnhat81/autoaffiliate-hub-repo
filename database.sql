CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    aff_link TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    order_id TEXT NOT NULL,
    amount REAL NOT NULL,
    commission REAL NOT NULL,
    status TEXT DEFAULT 'pending',
    tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_platform ON products(platform);
CREATE INDEX IF NOT EXISTS idx_order_platform ON orders(platform);

INSERT INTO products (platform, name, price, aff_link) VALUES ('shopee', 'Health Products', 500000, 'https://s.shopee.vn/1VpwtZktot?af=17314500392');
INSERT INTO orders (platform, order_id, amount, commission) VALUES ('shopee', 'ORD123', 20000000, 1000000);