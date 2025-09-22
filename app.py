from flask import Flask, request, jsonify
import os
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Config
SHOPEE_AFFILIATE_ID = os.environ.get('SHOPEE_AFFILIATE_ID', '17314500392')
DB_FILE = 'affiliate.db'

# Init Database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    with open('database.sql', 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return jsonify({'message': 'AutoAffiliate Hub is running! Call /fetch_shopee_products for Shopee links with Affiliate ID 17314500392.'})

@app.route('/fetch_shopee_products', methods=['GET'])
def fetch_shopee_products():
logger.info("Processing /fetch_shopee_products request")
    products_data = [
        {'name': 'Health Products', 'price': 500000, 'link': 'https://s.shopee.vn/1VpwtZktot'},
        {'name': 'Fashion Accessories', 'price': 300000, 'link': 'https://s.shopee.vn/3fuRTYceQK'},
        {'name': 'Home Appliances', 'price': 2000000, 'link': 'https://s.shopee.vn/3qDrfrc15N'},
        {'name': 'Men Clothes', 'price': 600000, 'link': 'https://s.shopee.vn/3LHb4wdv6I'},
        {'name': 'Men Shoes', 'price': 800000, 'link': 'https://s.shopee.vn/3Vb1HFdHlL'},
        {'name': 'Mobile & Gadgets', 'price': 15000000, 'link': 'https://s.shopee.vn/30ekgKfBmG'},
        {'name': 'Women Bags', 'price': 700000, 'link': 'https://s.shopee.vn/3AyAsdeYRJ'},
        {'name': 'Women Clothes', 'price': 500000, 'link': 'https://s.shopee.vn/2g1uHigSSE'},
        {'name': 'Women Shoes', 'price': 900000, 'link': 'https://s.shopee.vn/2qLKU1fp7H'},
        {'name': 'Men Bags', 'price': 600000, 'link': 'https://s.shopee.vn/50Pp40XZii'},
        {'name': 'Watches', 'price': 1000000, 'link': 'https://s.shopee.vn/5AjFGJWwNl'},
        {'name': 'Grocery', 'price': 200000, 'link': 'https://s.shopee.vn/4fmyfOYqOg'},
        {'name': 'Beauty', 'price': 400000, 'link': 'https://s.shopee.vn/4q6OrhYD3j'},
        {'name': 'Moms, Kids & Babies', 'price': 300000, 'link': 'https://s.shopee.vn/4LA8Gma74e'},
        {'name': 'Consumer Electronics', 'price': 3000000, 'link': 'https://s.shopee.vn/4VTYT5ZTjh'},
        {'name': 'Cameras', 'price': 5000000, 'link': 'https://s.shopee.vn/40XHsAbNkc'},
        {'name': 'Home & Living', 'price': 1000000, 'link': 'https://s.shopee.vn/4Aqi4TakPf'}
    ]
    products = []
    conn = sqlite3.connect(DB_FILE)
    for item in products_data:
        aff_link = f"{item['link']}?af={SHOPEE_AFFILIATE_ID}"
        products.append({'name': item['name'], 'price': item['price'], 'aff_link': aff_link})
        conn.execute("INSERT INTO products (platform, name, price, aff_link) VALUES (?, ?, ?, ?)",
                     ('shopee', item['name'], item['price'], aff_link))
    conn.commit()
    conn.close()
    logger.info("Successfully processed /fetch_shopee_products")
    return jsonify(products)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)