import unittest
import sqlite3
from flask import redirect, url_for, request
from shop import app
from threading import Thread
import time
import requests
from urlparse import urlparse

class Tests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        app.secret_key = "secret key"
        self.app = app.test_client()

    def tearDown(self):
        pass
    
    # def test_clientID(self):
    #     tester = app.test_client(self)
    #     response = tester.get('/', content_type='text/html; charset=utf-8')
    #     self.assertEqual(response.status_code, 200)

    # def test_product_page_loads(self):
    #     tester = app.test_client(self)
    #     response = tester.get('/', content_type='text/html; charset=utf-8')
    #     self.assertTrue(response.content_type, "text/html; charset=utf-8")

    def test_confirm_login(self):
        tester = app.test_client(self)
        # case valid input
        response = tester.post(
            '/confirm_login',
            data = dict(customerID=999),
            follow_redirects=False
            )
        expectedPath = '/products'
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, expectedPath)

        # case invalid input
        response = tester.post(
            '/confirm_login',
            data = dict(customerID=123),
            follow_redirects=False
            )
        expectedPath = '/login'
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, expectedPath)


    def test_add_product_to_cart(self):
        tester = app.test_client(self)
        response = tester.post(
            '/add',
            data = dict(quantity=2, productID=1),
            follow_redirects=True
            )
        # check cart if empty
        self.assertNotIn(b'Your Cart is Empty', response.data)
        # check cart total price
        with tester.session_transaction() as session:
            self.assertEqual(session['all_total_price'],20)        

    def test_purchase(self):   
        tester = app.test_client(self)
        with tester.session_transaction() as session:
            session['cart_item'] = {'1': {'total_price': 10, 'quantity': 1, 'unitPrice': 10, 'productDesc': 'apple', 'productID': 1}}
        # function will print updated stock detals in terminal    
        response = tester.get(
                '/purchase',
                data = session['cart_item'],
                follow_redirects=True
            )
        # confirm database changes and clear cart
        self.assertIn(b'Purchased sucessfully!', response.data)


    def test_multi_clients(self):
        def start_and_init_server(app):
            app.run(threaded=True)
        
        server_thread = Thread(target=start_and_init_server, args=(self.app, ))

        # number of requests
        n_requests = 5

        request_threads = []
        try:
            def get_page():
                tester = app.test_client(self)
                response = tester.get('/', content_type='text/html; charset=utf-8')
                self.assertEqual(response.status_code, 200)

            for i in range(n_requests):
                t = Thread(target=get_page)
                request_threads.append(t)
                t.start()

            all_done = False
            while not all_done:
                all_done = True
                for t in request_threads:
                    if t.is_alive():
                        all_done = False
                        time.sleep(1)

        except Exception, ex:
            print 'Something went horribly wrong!', ex.message

        finally:
            # stop all running threads
            server_thread._Thread__stop()
            for t in request_threads:
                t._Thread__stop()

    def test_multi_purchases(self):
        def start_and_init_server(app):
            app.run(threaded=True)
        
        server_thread = Thread(target=start_and_init_server, args=(self.app, ))

        # number of requests
        n_requests = 5

        request_threads = []
        try:
            def test_purchase():   
                tester = app.test_client(self)
                with tester.session_transaction() as session:
                    session['cart_item'] = {'1': {'total_price': 10, 'quantity': 1, 'unitPrice': 10, 'productDesc': 'apple', 'productID': 1}}
                # function will print updated stock detals in terminal    
                response = tester.get(
                        '/purchase',
                        data = session['cart_item'],
                        follow_redirects=True
                    )
                # confirm database changes and clear cart
                self.assertIn(b'Purchased sucessfully!', response.data)

            for i in range(n_requests):
                t = Thread(target=test_purchase)
                request_threads.append(t)
                t.start()

            all_done = False
            while not all_done:
                all_done = True
                for t in request_threads:
                    if t.is_alive():
                        all_done = False
                        time.sleep(1)

        except Exception, ex:
            print 'Something went horribly wrong!', ex.message

        finally:
            # stop all running threads
            server_thread._Thread__stop()
            for t in request_threads:
                t._Thread__stop()
    
    def test_confirm_purchase(self):
        tester = app.test_client(self)
        # case valid input
        response = tester.post(
            '/confirm_payment',
            data = dict(cardNo=1234567812345678, cardExpMM=11, cardExpYY=23),
            follow_redirects=False
            )
        expectedPath = '/purchase'
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, expectedPath)

        # case invalid input
        response = tester.post(
            '/confirm_payment',
            data = dict(cardNo=1234567812345678, cardExpMM=11, cardExpYY=20),
            follow_redirects=False
            )
        expectedPath = '/payment'
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, expectedPath)

if __name__ == '__main__':
    unittest.main()