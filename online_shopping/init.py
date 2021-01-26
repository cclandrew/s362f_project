import sqlite3

conn = sqlite3.connect('shop.db')
cur = conn.cursor()

### PRODUCTS

# cur.execute("""CREATE TABLE products(
#                 productID integer,
#                 productDesc text,
#                 unitPrice integer,
#                 quantityInStock integer
#                 )""")
# cur.execute("INSERT INTO products VALUES (001,'apple',10,100)")
# cur.execute("INSERT INTO products VALUES (002,'orange',12,100)")
# cur.execute("INSERT INTO products VALUES (003,'banana',15,100)")
# cur.execute("INSERT INTO products VALUES (004,'pizza',20,100)")
# cur.execute("INSERT INTO products VALUES (005,'burger',25,100)")
# cur.execute("INSERT INTO products VALUES (006,'juice',15,50)")
# cur.execute("INSERT INTO products VALUES (007,'cola',15,50)")
# cur.execute("INSERT INTO products VALUES (008,'watermelon',20,50)")
# cur.execute("INSERT INTO products VALUES (009,'pineapple',25,50)")
# cur.execute("INSERT INTO products VALUES (010,'cheese',30,50)")
# cur.execute("UPDATE products SET quantityInStock = 4 WHERE productID = 001")
cur.execute("SELECT * FROM products")
print(cur.fetchall())

### CUSTOMERS

# cur.execute("""CREATE TABLE customers(
#                 customerID integer
#                 )""")
# cur.execute("INSERT INTO customers VALUES (999)")
# cur.execute("INSERT INTO customers VALUES (666)")
# cur.execute("SELECT * FROM customers")
# print(cur.fetchall())

conn.commit()
conn.close()