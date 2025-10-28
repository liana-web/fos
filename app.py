from flask import Flask, render_template, request, redirect, url_for, flash
from flask_scss import Scss
from flask_sqlalchemy import SQLAlchemy
import sqlite3

app = Flask (__name__)
app.secret_key = 'liana1234' # required for flashing messages
DB_NAME = 'fos.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()

        # Customers table
        c.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL
            )
        ''')

        # Create Products table
        c.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                image_url TEXT
            )
        ''')

        # Create Orders table
        c.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                order_date TEXT NOT NULL,
                order_status TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
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
                INSERT INTO products (name, price, image_url)
                VALUES (?, ?, ?)
            ''', [
                ('Crispy Pata', 850.00, 'pata.jpg'),
                ('Adobo', 350.00, 'adobo.jpg'),
                ('Kare-kare', 299.00, 'karekare.jpg'),
                ('Sisig', 180.00, 'sisig.jpg')
            ])
            conn.commit()


def get_products():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('SELECT id, name, price, image_url FROM products')
        return c.fetchall()

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    
    user = session.get('username')  # Try to get username from session
    if not user:
        user = "Guest"  # Default if no user is found
    return render_template('home.html', user=user)

@app.route('/register')
def register():
    return render_template('home.html')

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
                c.name, c.email
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
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

    
@app.route("/add_order", methods=["GET", "POST"])
def add_order():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Fetch products and customers
    c.execute("SELECT * FROM products")
    products = c.fetchall()

    c.execute("SELECT * FROM customers")
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
        selected_products = request.form.getlist("product_id")
        quantities = request.form.getlist("quantity")

        # Create order
        c.execute(
            "INSERT INTO orders (order_date, order_status, customer_id) VALUES (?, ?, ?)",
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


@app.route('/menu')
def menu():
    return render_template('menu.html')
    
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
    