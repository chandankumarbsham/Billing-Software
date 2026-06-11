# app.py
from flask import Flask, render_template, request
import oracledb
import os

app = Flask(__name__)

# Oracle Client
oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient")

def get_connection():
    return oracledb.connect(
        user=os.getenv("DB_USER", "billing_user"),
        password=os.getenv("DB_PASS", "billing123"),
        dsn=os.getenv("DB_DSN", "localhost:1521/orcldee")
    )

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/add_bill', methods=['POST'])
def add_bill():
    customer = request.form['customer']
    phone = request.form['phone']
    products = request.form.getlist('product[]')
    prices = request.form.getlist('price[]')
    quantities = request.form.getlist('quantity[]')

    conn = get_connection()
    cursor = conn.cursor()

    total_bill = 0
    cart = []

    for i in range(len(products)):
        try:
            price = int(prices[i])
            qty = int(quantities[i])
        except:
            return "Invalid input"

        total = price * qty
        total_bill += total

        cart.append({
            "product": products[i],
            "price": price,
            "quantity": qty,
            "total": total
        })

    cursor.execute(
        "INSERT INTO bills (customer_name, phone, total, bill_date) VALUES (:1, :2, :3, SYSDATE)",
        (customer, phone, total_bill)
    )

    cursor.execute("SELECT bills_seq.CURRVAL FROM dual")
    bill_id = cursor.fetchone()[0]

    for item in cart:
        cursor.execute(
            """INSERT INTO bill_items (id, product_name, price, quantity, total)
               VALUES (:1, :2, :3, :4, :5)""",
            (bill_id, item["product"], item["price"], item["quantity"], item["total"])
        )

    conn.commit()
    cursor.close()
    conn.close()

    return render_template("bill.html", cart=cart, total=total_bill, customer=customer, phone=phone)

@app.route('/history')
def history():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, total, bill_date FROM bills ORDER BY id DESC")
    bills = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("history.html", bills=bills)

if __name__ == "__main__":
    app.run(debug=True)