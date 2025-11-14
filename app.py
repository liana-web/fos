import os
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_scss import Scss
from flask_sqlalchemy import SQLAlchemy

app = Flask (__name__)
app.secret_key = 'liana1234' # required for flashing messages

DB_NAME = 'fos.db'
UPLOAD_FOLDER = 'static/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()

        # Users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                role INTEGER DEFAULT 2)''')  # 1 = admin, 2 = customer

        # Create Products table
        c.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price REAL NOT NULL,
                image_url TEXT
            )
        ''')

        # Create Orders table
        c.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                order_date TEXT NOT NULL,
                order_status TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Create Order Items table
        c.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')

        # Seed products with images if empty
        c.execute('SELECT COUNT(*) FROM products')
        if c.fetchone()[0] == 0:
            c.executemany('''
                INSERT INTO products (name, description, price, image_url)
                VALUES (?, ?, ?, ?)
            ''', [
                ('Crispy Pata', 'Deep-fried pork knuckle, boiled until tender then fried to achieve maximum crispness.', 850.00, 'pata.jpg'),
                ('Adobo', 'Pork braised in soy sauce, vinegar, crushed garlic, bay leaves, and peppercorns. (Serves 2–3)', 350.00, 'adobo.jpg'),
                ('Tokwa\'t Baboy', 'Crispy Lechon Kawali and deep-fried tofu in a tangy soy-vinegar dressing with onions and chili. (Serves 2–3)', 350.00, 'baboy.jpg'),
                ('Kare-kare', 'Oxtail and tripe stewed in a thick, savory peanut-based sauce. Served with bagoong. (Serves 3–4)', 299.00, 'karekare.jpg'),
                ('Sisig', 'Chopped pork cheek, onions, chili, and calamansi, served on a sizzling platter with a raw egg. (Serves 2–3)', 180.00, 'sisig.jpg'),
                ('Pork BBQ Skewers', 'Sweet, savory, and tender pork slices marinated and grilled over charcoal. (Price is per stick)', 80.00, 'bbq.jpg'),
                ('Bulalo (Beef Shank Soup)', 'Sweet, savory, and tender pork slices marinated and grilled over charcoal. (Price is per stick)', 550.00, 'bulalo.jpg')
            ])

        # Seed users if empty
        admin_password = generate_password_hash('adminpass')
        customer1_password = generate_password_hash('cust1pass')
        customer2_password = generate_password_hash('cust2pass')

        c.execute('SELECT COUNT(*) FROM users')
        if c.fetchone()[0] == 0:
            c.executemany('''
                INSERT INTO users (username, password, email, full_name, role)
                VALUES (?, ?, ?, ?, ?)
            ''', [
                ('admin', admin_password, 'admin@test.com', 'Admin User', 1),
                ('customer1', customer1_password, 'juliana@test.com', 'Juliana Ritz', 2),
                ('customer2', customer2_password, 'julianne@test.com', 'Julianne Curtis', 2)
            ])
            conn.commit()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/products/new', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']

        file = request.files['image_file']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # store path for db
            image_url = filename
        else:
            return "Invalid file type", 400

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            INSERT INTO products (name, description, price, image_url)
            VALUES (?, ?, ?, ?)
        """, (name, description, price, image_url))
        conn.commit()
        conn.close()

        return redirect('/products/list')

    return render_template('add_product.html')

@app.route('/products/list')
def product_list():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    products = c.execute("SELECT * FROM products").fetchall()
    conn.close()
    return render_template("product_list.html", products=products)

@app.route('/products/delete/<int:id>')
def delete_product(id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect('/products/list')

@app.route('/products/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    product = c.execute("SELECT * FROM products WHERE id = ?", (id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']

        # Check if new image uploaded
        file = request.files['image_file']
        if file and file.filename != '':
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                image_url = f"static/img/{filename}"
            else:
                return "Invalid file type", 400
        else:
            # keep old image
            image_url = product[4]

        conn.execute("""
            UPDATE products 
            SET name = ?, description = ?, price = ?, image_url = ?
            WHERE id = ?
        """, (name, description, price, image_url, id))
        conn.commit()
        conn.close()

        return redirect('/products/list')

    conn.close()
    return render_template("edit_product.html", product=product)


@app.route("/")
def index():
    return render_template('index.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["username"] = user[1]
            session["role"] = user[5]

            if session["role"] == 1:
                return redirect(url_for("add_order"))
            else:
                return redirect(url_for("add_order_customer"))
        else:
            flash("Invalid username or password", "danger")

    return render_template("index.html")

@app.route("/logout")
def logout():
    # Clear all session data
    session.clear()
    flash("You’ve been logged out.", "info")
    return redirect(url_for("login"))

@app.route('/home')
def home():
    
    user = session.get('username')  # Try to get username from session
    if not user:
        user = "Guest"  # Default if no user is found
    return render_template('home.html', user=user)

@app.route('/register')
def register():
    return render_template('home.html')

@app.route("/register_customer", methods=["GET", "POST"])
def register_customer():
    if request.method == "POST":
        full_name = request.form["full_name"]
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        if not full_name or not username or not password:
            flash("All fields are required!", "warning")
            return redirect(url_for("register_customer"))

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        try:
            c.execute(
                "INSERT INTO users (username, password, email, full_name, role) VALUES (?, ?, ?, ?, ?)",
                (username, password, email, full_name, 2)
            )
            conn.commit()
            flash("Customer registered successfully!", "success")
        except sqlite3.IntegrityError:
            flash("Username already exists. Please choose another.", "danger")
        finally:
            conn.close()

        return redirect(url_for("register_customer"))

    return render_template("register_customer.html")


@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    """Add new customer"""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO customers (name, email) VALUES (?, ?)', (name, email))
            conn.commit()
            flash("✅ User added successfully!", "success")
        except sqlite3.IntegrityError:
            return "Email already exists!"
        finally:
            conn.close()
        return redirect(url_for('add_customer'))

    return render_template('add_customer.html')

@app.route('/orders')
def view_orders():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT 
                o.id, o.order_date, o.order_status,
                u.full_name, u.email
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE u.role = 2
            ORDER BY o.id DESC
        ''')
        orders = c.fetchall()

        # Fetch products for each order
        order_data = []
        for order in orders:
            order_id = order[0]
            c.execute('''
                SELECT p.name, oi.quantity, p.price
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = ?
            ''', (order_id,))
            items = c.fetchall()
            total = sum(q * price for (name, q, price) in items)
            order_data.append({
                'id': order_id,
                'date': order[1],
                'status': order[2],
                'name': order[3],
                'email': order[4],
                'items': items,
                'total': total
            })

    return render_template('view_orders.html', orders=order_data)

@app.route('/my-orders')
def customer_orders():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT 
                o.id, o.order_date, o.order_status,
                u.full_name, u.email
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE u.role = 2 AND u.id = ?
            ORDER BY o.id DESC
        ''', (session["user_id"],))
        orders = c.fetchall()

        # Fetch products for each order
        order_data = []
        for order in orders:
            order_id = order[0]
            c.execute('''
                SELECT p.name, oi.quantity, p.price
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = ?
            ''', (order_id,))
            items = c.fetchall()
            total = sum(q * price for (name, q, price) in items)
            order_data.append({
                'id': order_id,
                'date': order[1],
                'status': order[2],
                'name': order[3],
                'email': order[4],
                'items': items,
                'total': total
            })

    return render_template('view_orders.html', orders=order_data)

    
@app.route("/add_order", methods=["GET", "POST"])
def add_order():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Fetch products and customers
    c.execute("SELECT * FROM products")
    products = c.fetchall()

    c.execute("SELECT * FROM users WHERE role=2")
    customers = c.fetchall()

    if request.method == "POST":
        # Determine if new customer or existing
        customer_id = request.form.get("customer_id")
        new_name = request.form.get("new_name")
        new_email = request.form.get("new_email")

        if customer_id == "new":  # new customer chosen
            c.execute("INSERT INTO customers (name, email) VALUES (?, ?)", (new_name, new_email))
            customer_id = c.lastrowid

        order_date = request.form.get("order_date")
        order_status = request.form.get("order_status")
        selected_products = request.form.getlist("product_id[]")
        quantities = request.form.getlist("quantity[]")

        # Create order
        c.execute(
            "INSERT INTO orders (order_date, order_status, user_id) VALUES (?, ?, ?)",
            (order_date, order_status, customer_id),
        )
        order_id = c.lastrowid

        # Insert items
        for product_id, qty in zip(selected_products, quantities):
            if int(qty) > 0:
                c.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)",
                    (order_id, product_id, qty),
                )

        conn.commit()
        conn.close()
        return redirect(url_for("view_orders"))

    conn.close()
    return render_template("add_order.html", products=products, customers=customers)

@app.route("/add_order/customer", methods=["GET", "POST"])
def add_order_customer():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Fetch products and customers
    c.execute("SELECT * FROM products")
    products = c.fetchall()

    if request.method == "POST":
        order_date = datetime.now()
        order_status = 'Pending'
        selected_products = request.form.getlist("product_id[]")
        quantities = request.form.getlist("quantity[]")

        # Create order
        c.execute(
            "INSERT INTO orders (order_date, order_status, user_id) VALUES (?, ?, ?)",
            (order_date, order_status, session["user_id"]),
        )
        order_id = c.lastrowid

        # Insert items
        for product_id, qty in zip(selected_products, quantities):
            if int(qty) > 0:
                c.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)",
                    (order_id, product_id, qty),
                )

        conn.commit()
        conn.close()
        return redirect(url_for("customer_orders"))

    conn.close()
    return render_template("add_order_customer.html", products=products)


@app.route('/menu')
def menu():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Fetch products and customers
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    
    conn.commit()
    conn.close()
    return render_template('menu.html', products=products)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
    