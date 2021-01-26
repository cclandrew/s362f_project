import sqlite3
from flask import Flask, render_template, session, flash, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import time
from random import randint
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.secret_key = "secret key"

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def array_merge( first_array , second_array ):
	if isinstance( first_array , list ) and isinstance( second_array , list ):
		return first_array + second_array
	elif isinstance( first_array , dict ) and isinstance( second_array , dict ):
		return dict( list( first_array.items() ) + list( second_array.items() ) )
	elif isinstance( first_array , set ) and isinstance( second_array , set ):
		return first_array.union( second_array )
	return False

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=5)

@app.route('/')
@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/confirm_login', methods=['POST'])
def confirm_login():
    try:
        _customerID = int(request.form['customerID'])
        conn = sqlite3.connect('shop.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM customers WHERE customerID = ? ",(_customerID,))
        row = cur.fetchone()
        if row == None:
            flash('No such customer ID!')
            return redirect(url_for('.login'))
        else:
            return redirect(url_for('.products'))

    except Exception as e:
        print(e)

    finally: 
        cur.close()
        conn.close()


@app.route('/products')
def products():
    try:
        conn = sqlite3.connect('shop.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM products")
        rows = cur.fetchall()
        return render_template('products.html',products=rows)

    except Exception as e:
        print(e)

    finally: 
        cur.close()
        conn.close()

@app.route('/add', methods=['POST'])
def add_product_to_cart():
    try:
        cur = None
        _quantity = int(request.form['quantity'])
        _productID = request.form['productID']
        if _quantity and _productID and request.method == 'POST':
            conn = sqlite3.connect('shop.db')
            conn.row_factory = dict_factory
            cur = conn.cursor()
            cur.execute("SELECT * FROM products WHERE productID=?", (_productID,))
            row = cur.fetchone()
            
            itemArray = { row['productID'] : {'productDesc' : row['productDesc'], 'productID' : row['productID'], 'quantity' : _quantity, 'unitPrice' : row['unitPrice'], 'total_price': _quantity * row['unitPrice']}}
            
            all_total_price = 0
            all_total_quantity = 0
            
            session.modified = True
            if 'cart_item' in session:
                if row['productID'] in session['cart_item']:
                    for key, value in session['cart_item'].items():
                        if row['productID'] == key:
                            old_quantity = session['cart_item'][key]['quantity']
                            total_quantity = old_quantity + _quantity
                            session['cart_item'][key]['quantity'] = total_quantity
                            session['cart_item'][key]['total_price'] = total_quantity * row['unitPrice']
                else:
                    session['cart_item'] = array_merge(session['cart_item'], itemArray)

                for key, value in session['cart_item'].items():
                    individual_quantity = int(session['cart_item'][key]['quantity'])
                    individual_price = float(session['cart_item'][key]['total_price'])
                    all_total_quantity = all_total_quantity + individual_quantity
                    all_total_price = all_total_price + individual_price
            else:
                session['cart_item'] = itemArray
                all_total_quantity = all_total_quantity + _quantity
                all_total_price = all_total_price + _quantity * row['unitPrice']
            
            session['all_total_quantity'] = all_total_quantity
            session['all_total_price'] = all_total_price
            flash('Added items to cart sucessfully!')
            return redirect(url_for('.products'))
        else:
            return 'Error while adding item to cart'

    except Exception as e:
        print(e)
        
    finally:
        cur.close() 
        conn.close()

@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/confirm_payment', methods=['POST'])
def confirm_payment():
    _cardNo = request.form['cardNo']
    _cardExpMM = request.form['cardExpMM']
    _cardExpYY = request.form['cardExpYY']
    exp_str = '01/' + _cardExpMM + '/' + _cardExpYY 
    exp_obj = datetime.strptime(str(exp_str), '%d/%m/%y').date()
    now = datetime.now().date()
    if len(_cardNo) == 16 and exp_obj > now and request.method == 'POST':   
        return redirect(url_for('.purchase'))
    else:
        flash('Card info invalid!')
        return redirect(url_for('.payment'))


@app.route('/purchase')
def purchase():
    try:
        cur = None
        session.modified = True
        if 'cart_item' in session:
            conn = sqlite3.connect('shop.db')
            cur = conn.cursor()
            
            for key, value in session['cart_item'].items():
                individual_productID = session['cart_item'][key]['productID']
                individual_quantity = int(session['cart_item'][key]['quantity'])
                individual_productDesc = session['cart_item'][key]['productDesc']
                time.sleep(randint(2,4))
                cur.execute("SELECT quantityInStock FROM products WHERE productID=?", (individual_productID,))
                results = cur.fetchone()
                old_quantity = results[0]
                restock = 100
                if old_quantity >= individual_quantity and old_quantity >= 0:
                    new_quantity = old_quantity - individual_quantity
                    cur.execute("UPDATE products SET quantityInStock = ? WHERE productID = ?",(new_quantity,individual_productID,))
                    conn.commit()
                    print 'Updated product id: ' , individual_productID , ', New quantity: ' , new_quantity
                    break
                elif old_quantity == 0:
                    print individual_productDesc, 'out of stock! replenished stock!'
                    cur.execute("UPDATE products SET quantityInStock = ? WHERE productID = ?",(restock,individual_productID,))
                    conn.commit()
                    flash('Error while making puchase: out of stock! Stock replenished! Please try again!')
                    return redirect(url_for('.products'))
                    break
                    
                else:
                    flash('Error while making puchase: Not enough stock for requested quantity')
                    return redirect(url_for('.products'))
                    break


            session.clear()
            flash('Purchased sucessfully!')
            return redirect(url_for('.products'))

        else:
            return 'Error while making puchase'
    
    except Exception as e:
        print(e)
        
    finally:
        cur.close() 
        conn.close()
        
@app.route('/empty')
def empty_cart():
    session.clear()
    return redirect(url_for('.products'))

@app.route('/delete/<string:productID>')
def delete_product(productID):
	try:
		all_total_price = 0
		all_total_quantity = 0
		session.modified = True
		
		for item in session['cart_item'].items():
			if item[0] == productID:				
				session['cart_item'].pop(item[0], None)
				if 'cart_item' in session:
					for key, value in session['cart_item'].items():
						individual_quantity = int(session['cart_item'][key]['quantity'])
						individual_price = float(session['cart_item'][key]['total_price'])
						all_total_quantity = all_total_quantity + individual_quantity
						all_total_price = all_total_price + individual_price
				break
		
		if all_total_quantity == 0:
			session.clear()
		else:
			session['all_total_quantity'] = all_total_quantity
			session['all_total_price'] = all_total_price
		
		return redirect(url_for('.products'))
	except Exception as e:
		print(e)
		

    
if __name__ == '__main__':
    app.run(debug=True)