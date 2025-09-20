import requests
import json
import hmac
import hashlib
import time
import sqlite3
from flask import Flask, request, jsonify
from urllib.parse import urlencode, quote
from aws_requests_auth.aws_auth import AWSRequestsAuth
from datetime import datetime
import feedparser  # Đã cài

app = Flask(__name__)

# Config (chỉ cần Affiliate ID từ affiliate.shopee.vn)
SHOPEE_AFFILIATE_ID = '17314500392'  # Lấy từ https://affiliate.shopee.vn/
SHOPEE_SHOP_ID = 'nhatquynh2009'  # Dùng shop mẫu (thay bằng shop phổ biến nếu biết)
AMAZON_ACCESS_KEY = 'YOUR_ACCESS_KEY_ID'
AMAZON_SECRET_KEY = 'YOUR_SECRET_ACCESS_KEY'
AMAZON_ASSOCIATE_TAG = 'YOUR_ASSOCIATE_TAG'
AMAZON_HOST = 'webservices.amazon.com'
AMAZON_REGION = 'us-east-1'
AMAZON_SERVICE = 'paapi5'
FB_PAGE_ID = 'YOUR_FB_PAGE_ID'
FB_ACCESS_TOKEN = 'YOUR_FB_PAGE_ACCESS_TOKEN'
DB_FILE = 'affiliate.db'

# Init Database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    with open('database.sql', 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

init_db()

@app.route('/fetch_shopee_products', methods=['GET'])
def fetch_shopee_products():
    # Thay thế: Sử dụng RSS hoặc hardcode hot products
    # RSS ví dụ (thay bằng RSS thật từ Shopee search nếu có)
    rss_url = 'https://shopee.vn/rss/category/1103'  # Điện thoại; dùng search RSS nếu tìm được
    feed = feedparser.parse(rss_url)
    products = []
    conn = sqlite3.connect(DB_FILE)
    if not feed.entries:  # Nếu RSS không hoạt động, dùng hardcode mẫu
        products_data = [
            {'name': 'iPhone 15', 'price': 20000000, 'item_id': '123456'},
            {'name': 'Samsung Galaxy S23', 'price': 18000000, 'item_id': '654321'}
        ]
        for item in products_data:
            aff_link = f"https://shopee.vn/product-i.{SHOPEE_SHOP_ID}.{item['item_id']}?af={SHOPEE_AFFILIATE_ID}"
            products.append({'name': item['name'], 'price': item['price'], 'aff_link': aff_link})
            conn.execute("INSERT INTO products (platform, name, price, aff_link) VALUES (?, ?, ?, ?)",
                         ('shopee', item['name'], item['price'], aff_link))
    else:
        for entry in feed.entries[:10]:
            name = entry.title
            price = 20000000  # Parse từ entry.description nếu có (sử dụng regex)
            item_id = '123456'  # Extract từ entry.link, ví dụ: re.search(r'i\.(\d+)\.(\d+)', entry.link)
            aff_link = f"https://shopee.vn/product-i.{SHOPEE_SHOP_ID}.{item_id}?af={SHOPEE_AFFILIATE_ID}"
            products.append({'name': name, 'price': price, 'aff_link': aff_link})
            conn.execute("INSERT INTO products (platform, name, price, aff_link) VALUES (?, ?, ?, ?)",
                         ('shopee', name, price, aff_link))
    conn.commit()
    conn.close()
    return jsonify(products)

@app.route('/fetch_amazon_products', methods=['GET'])
def fetch_amazon_products():
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
        return jsonify(products)
    return jsonify({'error': response.text}), response.status_code

@app.route('/post_to_facebook', methods=['POST'])
def post_to_facebook():
    data = request.json
    message = data.get('message', 'Sản phẩm hot!')
    link = data.get('link')
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/feed"
    params = {'message': message, 'link': link, 'access_token': FB_ACCESS_TOKEN}
    response = requests.post(url, data=params)
    return jsonify(response.json())

@app.route('/track_order_webhook', methods=['POST'])
def track_order_webhook():
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
    return jsonify({'status': 'tracked'})

@app.route('/get_orders', methods=['GET'])
def get_orders():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    conn.close()
    return jsonify([{'id': o[0], 'platform': o[1], 'order_id': o[2], 'amount': o[3], 'commission': o[4], 'status': o[5], 'tracked_at': o[6]} for o in orders])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)