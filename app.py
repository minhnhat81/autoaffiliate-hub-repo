from flask import Flask, request, jsonify
import os
import sqlite3
from urllib.parse import urlencode, quote
from aws_requests_auth.aws_auth import AWSRequestsAuth
import requests
from datetime import datetime
import logging

app = Flask(__name__)

# Config logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config (sử dụng Affiliate ID chính thức, các keys khác từ env hoặc placeholder)
SHOPEE_AFFILIATE_ID = os.environ.get('SHOPEE_AFFILIATE_ID', '17314500392')  # Affiliate ID chính thức của bạn
SHOPEE_SHOP_ID = os.environ.get('SHOPEE_SHOP_ID', '123456')  # Placeholder, thay bằng Shop ID thật nếu có
AMAZON_ACCESS_KEY = os.environ.get('AMAZON_ACCESS_KEY', 'YOUR_ACCESS_KEY_ID')
AMAZON_SECRET_KEY = os.environ.get('AMAZON_SECRET_KEY', 'YOUR_SECRET_ACCESS_KEY')
AMAZON_ASSOCIATE_TAG = os.environ.get('AMAZON_ASSOCIATE_TAG', 'YOUR_ASSOCIATE_TAG')
AMAZON_HOST = 'webservices.amazon.com'
AMAZON_REGION = 'us-east-1'
AMAZON_SERVICE = 'paapi5'
FB_PAGE_ID = os.environ.get('FB_PAGE_ID', 'YOUR_FB_PAGE_ID')
FB_ACCESS_TOKEN = os.environ.get('FB_ACCESS_TOKEN', 'YOUR_FB_PAGE_ACCESS_TOKEN')
DB_FILE = 'affiliate.db'

# Init Database with logging
def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        with open('database.sql', 'r') as f:
            conn.executescript(f.read())
        conn.commit()
        logger.info("Database initialized successfully")
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
    finally:
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

@app.route('/fetch_amazon_products', methods=['GET'])
def fetch_amazon_products():
    logger.info("Processing /fetch_amazon_products request")
    auth = AWSRequestsAuth(
        aws_access_key=AMAZON_ACCESS_KEY,
        aws_secret_access_key=AMAZON_SECRET_KEY,
        aws_host=AMAZON_HOST,
        aws_region=AMAZON_REGION,
        aws_service=AMAZON_SERVICE
    )
    url = f"https://{AMAZON_HOST}/paapi5/searchitems"
    headers = {'Content-Type': 'application/json', 'X-Amz-Target': 'com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems'}
    payload = {
        "Keywords": "smartphone",
        "Resources": ["ItemInfo.Title", "Offers.Listings.Price"],
        "PartnerTag": AMAZON_ASSOCIATE_TAG,
        "PartnerType": "Associates",
        "Marketplace": "www.amazon.com"
    }
    response = requests.post(url, auth=auth, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        products = []
        conn = sqlite3.connect(DB_FILE)
        for item in data.get('SearchResult', {}).get('Items', []):
            aff_link = f"https://www.amazon.com/dp/{item['ASIN']}?tag={AMAZON_ASSOCIATE_TAG}"
            price = item['Offers']['Listings'][0]['Price']['Amount'] if 'Offers' in item else 0.0
            products.append({'name': item['ItemInfo']['Title']['DisplayValue'], 'price': float(price), 'aff_link': aff_link})
            conn.execute("INSERT INTO products (platform, name, price, aff_link) VALUES (?, ?, ?, ?)",
                         ('amazon', item['ItemInfo']['Title']['DisplayValue'], float(price), aff_link))
        conn.commit()
        conn.close()
        logger.info("Successfully processed /fetch_amazon_products")
        return jsonify(products)
    logger.error(f"Failed to fetch Amazon products: {response.text}")
    return jsonify({'error': response.text}), response.status_code

@app.route('/post_to_facebook', methods=['POST'])
def post_to_facebook():
    logger.info("Processing /post_to_facebook request")
    data = request.json
    message = data.get('message', 'Sản phẩm hot!')
    link = data.get('link')
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/feed"
    params = {'message': message, 'link': link, 'access_token': FB_ACCESS_TOKEN}
    response = requests.post(url, data=params)
    if response.status_code == 200:
        logger.info("Successfully posted to Facebook")
    else:
        logger.error(f"Failed to post to Facebook: {response.text}")
    return jsonify(response.json())

@app.route('/track_order_webhook', methods=['POST'])
def track_order_webhook():
    logger.info("Processing /track_order_webhook request")
    data = request.json
    platform = data.get('platform', 'unknown')
    order_id = data['order_id']
    amount = data['amount']
    commission = data['commission']
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT INTO orders (platform, order_id, amount, commission) VALUES (?, ?, ?, ?)",
                 (platform, order_id, amount, commission))
    conn.commit()
    conn.close()
    logger.info("Successfully tracked order webhook")
    return jsonify({'status': 'tracked'})

@app.route('/get_orders', methods=['GET'])
def get_orders():
    logger.info("Processing /get_orders request")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    conn.close()
    logger.info(f"Retrieved {len(orders)} orders")
    return jsonify([{'id': o[0], 'platform': o[1], 'order_id': o[2], 'amount': o[3], 'commission': o[4], 'status': o[5], 'tracked_at': o[6]} for o in orders])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Sử dụng port từ Render, mặc định 10000 nếu không có
    app.run(host='0.0.0.0', port=port)