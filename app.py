import os
import json
from flask import Flask, request, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # change this in production
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# JSON storage files
USERS_FILE = "data.txt"         # keeping your current format for users
PRODUCTS_FILE = "products.json" # store product listings
CART_FILE = "carts.json"        # store user carts
PURCHASE_FILE = "purchases.json" # store purchase history

# Utility functions
def load_json(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# -----------------------------
# Registration
# -----------------------------
@app.route('/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        contact = request.form['contact']
        dob = request.form['dob']
        gender = request.form['gender']
        address = request.form['address']
        description = request.form['description']

        if password != confirm_password:
            return "❌ Passwords do not match."

        with open(USERS_FILE, 'a') as f:
            f.write(f"{email},{password},{contact},{dob},{gender},{address},{description},\n")

        return redirect(url_for('login'))

    return render_template('index.html')

# -----------------------------
# Login
# -----------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            with open(USERS_FILE, 'r') as f:
                users = f.readlines()

            for user in users:
                saved_email, saved_password, *_ = user.strip().split(',')
                if email == saved_email and password == saved_password:
                    session['user'] = email
                    return redirect(url_for('dashboard'))

            error = "❌ Invalid email or password."

        except FileNotFoundError:
            error = "❌ No users registered yet."

    return render_template('login.html', error=error)

# -----------------------------
# Dashboard
# -----------------------------
@app.route('/dashboard')
def dashboard():
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=user)

# -----------------------------
# Profile
# -----------------------------
@app.route('/profile/<user>', methods=['GET', 'POST'])
def profile(user):
    uploaded_image = None
    image_filename = f"{secure_filename(user)}.jpg"
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
    full_image_url = f"/{app.config['UPLOAD_FOLDER']}/{image_filename}"

    users = []
    current_user = None
    with open(USERS_FILE, 'r') as f:
        for line in f:
            parts = line.strip().split(',')
            if parts[0] == user:
                current_user = parts
            users.append(parts)

    if current_user is None:
        return "❌ No user data found."

    if request.method == 'POST':
        file = request.files['profile_image']
        if file:
            file.save(image_path)
            if len(current_user) < 8 or not current_user[7]:
                current_user = current_user[:7] + [image_filename]
                for i in range(len(users)):
                    if users[i][0] == user:
                        users[i] = current_user
                        break
                with open(USERS_FILE, 'w') as f:
                    for u in users:
                        f.write(','.join(u) + '\n')

    if os.path.exists(image_path):
        uploaded_image = full_image_url

    user_info = {
        'email': current_user[0],
        'contact': current_user[2],
        'dob': current_user[3],
        'gender': current_user[4],
        'address': current_user[5],
        'description': current_user[6],
    }

    return render_template('profile.html', user=user, user_info=user_info, uploaded_image=uploaded_image)

# -----------------------------
# About
# -----------------------------
@app.route('/about')
def about():
    user = session.get('user')
    return render_template('about.html', user=user)

# -----------------------------
# Product Feed + Search + Filter
# -----------------------------
@app.route('/products')
def products():
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))

    products = load_json(PRODUCTS_FILE).get("products", [])
    category = request.args.get("category")
    search = request.args.get("search")

    if category:
        products = [p for p in products if p["category"].lower() == category.lower()]
    if search:
        products = [p for p in products if search.lower() in p["title"].lower()]

    return render_template('products.html', user=user, products=products)

# -----------------------------
# Add Product
# -----------------------------
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        description = request.form['description']
        price = request.form['price']
        file = request.files['image']

        filename = None
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        products = load_json(PRODUCTS_FILE)
        if "products" not in products:
            products["products"] = []

        product = {
            "id": len(products["products"]) + 1,
            "title": title,
            "category": category,
            "description": description,
            "price": price,
            "image": filename or "default.png",
            "owner": user
        }
        products["products"].append(product)
        save_json(PRODUCTS_FILE, products)

        return redirect(url_for('products'))

    return render_template('add_product.html', user=user)

# -----------------------------
# Product Detail
# -----------------------------
@app.route('/product/<int:pid>')
def product_detail(pid):
    products = load_json(PRODUCTS_FILE).get("products", [])
    product = next((p for p in products if p["id"] == pid), None)
    if not product:
        return "❌ Product not found."
    return render_template('product_detail.html', product=product)

# -----------------------------
# My Listings
# -----------------------------
@app.route('/my_listings')
def my_listings():
    user = session.get('user')
    products = load_json(PRODUCTS_FILE).get("products", [])
    my_products = [p for p in products if p["owner"] == user]
    return render_template('my_listings.html', products=my_products, user=user)

# -----------------------------
# Cart
# -----------------------------
@app.route('/cart')
def cart():
    user = session.get('user')
    cart_data = load_json(CART_FILE).get(user, [])
    return render_template('cart.html', cart=cart_data, user=user)

@app.route('/add_to_cart/<int:pid>')
def add_to_cart(pid):
    user = session.get('user')
    carts = load_json(CART_FILE)
    if user not in carts:
        carts[user] = []
    carts[user].append(pid)
    save_json(CART_FILE, carts)
    return redirect(url_for('cart'))

# -----------------------------
# Purchases
# -----------------------------
@app.route('/purchases')
def purchases():
    user = session.get('user')
    purchases = load_json(PURCHASE_FILE).get(user, [])
    return render_template('purchases.html', purchases=purchases, user=user)

# -----------------------------
# Logout
# -----------------------------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# -----------------------------
# Run App
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)
