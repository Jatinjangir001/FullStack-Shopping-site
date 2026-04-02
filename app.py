import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from models import User
from bson.objectid import ObjectId

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'static/uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB max upload

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database connection
client = MongoClient(os.getenv('MONGO_URI', "mongodb://localhost:27017/mommys_herbal"))
db = client.get_database()
users_collection = db['users']
products_collection = db['products']
orders_collection = db['orders']

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({"_id": ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

# Template context processor
@app.context_processor
def utility_processor():
    def get_cart_count():
        return sum(item['quantity'] for item in session.get('cart', []))
    return dict(cart_count=get_cart_count())

@app.context_processor
def inject_new_orders_count():
    if current_user.is_authenticated and getattr(current_user, 'is_admin', False):
        try:
            count = orders_collection.count_documents({'is_new': True})
            return dict(new_orders_count=count)
        except Exception:
            pass
    return dict(new_orders_count=0)

# --- USER ROUTES ---
@app.route('/')
def index():
    search = request.args.get('search', '')
    category = request.args.get('category', 'All')
    
    query = {}
    if search:
        query['name'] = {'$regex': search, '$options': 'i'}
    if category and category != 'All':
        query['category'] = category
        
    products = list(products_collection.find(query))
    return render_template('index.html', products=products, current_category=category, search_query=search)

@app.route('/product/<product_id>')
def product_detail(product_id):
    product = products_collection.find_one({'_id': ObjectId(product_id)})
    if not product:
        flash('Product not found.', 'error')
        return redirect(url_for('index'))
        
    suggested_products = list(products_collection.find({'_id': {'$ne': ObjectId(product_id)}}).limit(4))
    
    return render_template('product.html', product=product, suggested_products=suggested_products)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        password = request.form.get('password')

        if users_collection.find_one({'email': email}):
            flash('Email address already exists', 'error')
            return redirect(url_for('register'))

        # password_hash = generate_password_hash(password)
        
        # Check if first user, make admin
        is_admin = users_collection.count_documents({}) == 0

        user_id = users_collection.insert_one({
            'name': name,
            'email': email,
            'mobile': mobile,
            'password': password,
            'is_admin': is_admin
        }).inserted_id

        user_data = users_collection.find_one({"_id": user_id})
        user = User(user_data)
        login_user(user)
        flash('Account created successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_data = users_collection.find_one({'email': email})
        
        if user_data and check_password_hash(user_data.get('password_hash', ''), password):
            user = User(user_data)
            login_user(user)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        
        flash('Please check your login details and try again.', 'error')
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

# --- ADMIN ROUTES ---
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access that page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    products = list(products_collection.find())
    return render_template('admin/dashboard.html', products=products)

@app.route('/admin/orders')
@login_required
@admin_required
def admin_orders():
    # Fetch all orders (newest first)
    orders = list(orders_collection.find().sort('_id', -1))
    
    # Enrich with user details
    for order in orders:
        user = users_collection.find_one({'_id': ObjectId(order['user_id'])})
        if user:
            order['user_name'] = user.get('name', 'Unknown')
            order['user_email'] = user.get('email', 'Unknown')
            order['user_mobile'] = user.get('mobile', 'Unknown')
        
    # Mark new orders as read/seen
    orders_collection.update_many({'is_new': True}, {'$set': {'is_new': False}})
            
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/product/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        category = request.form.get('category', 'Other')
        is_out_of_stock = 'out_of_stock' in request.form
        
        sizes_str = request.form.get('sizes', '')
        sizes = []
        for s in sizes_str.split(','):
            s = s.strip()
            if not s: continue
            if ':' in s:
                parts = s.split(':')
                try:
                    sizes.append({'size': parts[0].strip(), 'price': float(parts[1].strip())})
                except ValueError:
                    sizes.append({'size': parts[0].strip(), 'price': price})
            else:
                sizes.append({'size': s, 'price': price})
        
        # Handle Image
        image_url = ''
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_url = 'uploads/' + filename
                
        products_collection.insert_one({
            'name': name,
            'description': description,
            'price': price,
            'category': category,
            'sizes': sizes,
            'image_url': image_url,
            'is_out_of_stock': is_out_of_stock
        })
        flash('Product added successfully', 'success')
        return redirect(url_for('admin_dashboard'))
        
    return render_template('admin/product_form.html', product=None)

@app.route('/admin/product/edit/<product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    product = products_collection.find_one({'_id': ObjectId(product_id)})
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        category = request.form.get('category', 'Other')
        is_out_of_stock = 'out_of_stock' in request.form
        
        sizes_str = request.form.get('sizes', '')
        sizes = []
        for s in sizes_str.split(','):
            s = s.strip()
            if not s: continue
            if ':' in s:
                parts = s.split(':')
                try:
                    sizes.append({'size': parts[0].strip(), 'price': float(parts[1].strip())})
                except ValueError:
                    sizes.append({'size': parts[0].strip(), 'price': price})
            else:
                sizes.append({'size': s, 'price': price})
        
        update_data = {
            'name': name,
            'description': description,
            'price': price,
            'category': category,
            'sizes': sizes,
            'is_out_of_stock': is_out_of_stock
        }
        
        # Handle Image
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                update_data['image_url'] = 'uploads/' + filename
                
        products_collection.update_one({'_id': ObjectId(product_id)}, {'$set': update_data})
        flash('Product updated successfully', 'success')
        return redirect(url_for('admin_dashboard'))
        
    return render_template('admin/product_form.html', product=product)

@app.route('/admin/product/delete/<product_id>', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    products_collection.delete_one({'_id': ObjectId(product_id)})
    flash('Product deleted', 'success')
    return redirect(url_for('admin_dashboard'))

# --- CART & CHECKOUT ROUTES ---
@app.route('/cart/add/<product_id>', methods=['POST'])
def add_to_cart(product_id):
    size = request.form.get('size', '')
    quantity_to_add = int(request.form.get('quantity', 1))
    
    product = products_collection.find_one({'_id': ObjectId(product_id)})
    if not product or product.get('is_out_of_stock'):
        flash('Product unavailable', 'error')
        return redirect(request.referrer or url_for('index'))
        
    cart_price = product['price']
    if size and product.get('sizes'):
        for s in product['sizes']:
            if isinstance(s, dict) and s.get('size') == size:
                cart_price = s.get('price', product['price'])
                break
            elif isinstance(s, str) and s == size:
                cart_price = product['price']
                break

    if 'cart' not in session:
        session['cart'] = []
    
    cart = session['cart']
    
    item_found = False
    for item in cart:
        if item['product_id'] == product_id and item.get('size') == size:
            item['quantity'] += quantity_to_add
            item_found = True
            break
            
    if not item_found:
        cart.append({
            'product_id': product_id,
            'name': product['name'],
            'price': cart_price,
            'size': size,
            'quantity': quantity_to_add,
            'image_url': product.get('image_url', '')
        })
        
    session.modified = True
    flash(f"{product['name']} added to cart!", 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/cart')
def view_cart():
    cart = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    return render_template('cart.html', cart=cart, total=total)

@app.route('/cart/remove/<product_id>/<size>', methods=['POST'])
def remove_from_cart(product_id, size):
    if size == "None":
        size = ""
    cart = session.get('cart', [])
    session['cart'] = [item for item in cart if not (item['product_id'] == product_id and item.get('size', '') == size)]
    session.modified = True
    flash('Item removed from cart', 'success')
    return redirect(url_for('view_cart'))

@app.route('/cart/update/<product_id>/<size>', methods=['POST'])
def update_cart(product_id, size):
    if size == "None":
        size = ""
    quantity = int(request.form.get('quantity', 1))
    
    cart = session.get('cart', [])
    for item in cart:
        if item['product_id'] == product_id and item.get('size', '') == size:
            if quantity > 0:
                item['quantity'] = quantity
            else:
                cart.remove(item)
            break
            
    session['cart'] = cart
    session.modified = True
    flash('Cart updated', 'success')
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'POST':
        if 'cart' not in session or not session['cart']:
            flash('Your cart is empty', 'error')
            return redirect(url_for('view_cart'))
            
        shipping_address = {
            'house_no': request.form.get('house_no', ''),
            'street': request.form.get('street', ''),
            'landmark': request.form.get('landmark', ''),
            'city': request.form.get('city', ''),
            'state': request.form.get('state', ''),
            'pincode': request.form.get('pincode', '')
        }
            
        cart = session['cart']
        total = sum(item['price'] * item['quantity'] for item in cart)
        
        orders_collection.insert_one({
            'user_id': current_user.id,
            'items': cart,
            'total': total,
            'status': 'Processing',
            'shipping_address': shipping_address,
            'is_new': True
        })
        session['cart'] = []
        session.modified = True
        flash('Order placed successfully! Thank you for shopping with us.', 'success')
        return redirect(url_for('index'))
        
    cart = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    return render_template('checkout.html', total=total)

if __name__ == '__main__':
    app.run(debug=True)
    # app.run(debug=True, host='10.250.168.107')
#     # app.run(host="10.250.168.107", port=5000, debug=True)
# if __name__ == '__main__':
# #     app.run(host='127.0.0.1', port=5000, debug=True)
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True)