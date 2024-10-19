import unittest
import json
from app import app  

class FlaskAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app.test_client()
        cls.app.testing = True

    def test_signup_success(self):
        response = self.app.post('/signup', json={
            'email': 'uniqueuser@example.com',
            'username': 'uniqueuser',           
            'password': 'securepassword'
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn(b'Sign up successful', response.data)

    def test_signup_duplicate_email(self):
        self.app.post('/signup', json={
            'email': 'test@example.com',
            'username': 'testuser2',
            'password': 'securepassword2'
        })
        response = self.app.post('/signup', json={
            'email': 'test@example.com',
            'username': 'testuser3',
            'password': 'securepassword3'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Email already exists. Try a different email.', response.data)

    def test_signup_duplicate_username(self):
        
        self.app.post('/signup', json={
            'email': 'firstuser@example.com',
            'username': 'testuser',
            'password': 'securepassword'
        })

        
        response = self.app.post('/signup', json={
            'email': 'seconduser@example.com',
            'username': 'testuser',  
            'password': 'anotherpassword'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Username already exists', response.data)

    def test_signin_success(self):
        self.app.post('/signup', json={
            'email': 'signin@example.com',
            'username': 'signinuser',
            'password': 'securepassword'
        })
        response = self.app.post('/signin', json={
            'username': 'signinuser',
            'password': 'securepassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sign in successful', response.data)

    def test_signin_invalid_username(self):
        response = self.app.post('/signin', json={
            'username': 'invaliduser',
            'password': 'somepassword'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Username does not exist.', response.data)

    def test_signin_incorrect_password(self):
        self.app.post('/signup', json={
            'email': 'signin2@example.com',
            'username': 'signinuser2',
            'password': 'securepassword'
        })
        response = self.app.post('/signin', json={
            'username': 'signinuser2',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Incorrect password.', response.data)

    def test_deposit(self):
        self.app.post('/signup', json={
            'email': 'deposit@example.com',
            'username': 'deposituser',
            'password': 'securepassword'
        })
        self.app.post('/signin', json={
            'username': 'deposituser',
            'password': 'securepassword'
        })
        response = self.app.post('/deposit', json={
            'amount': 100.0
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Deposit successful', response.data)

    def test_withdraw(self):
        self.app.post('/signup', json={
            'email': 'withdraw@example.com',
            'username': 'withdrawuser',
            'password': 'securepassword'
        })
        self.app.post('/signin', json={
            'username': 'withdrawuser',
            'password': 'securepassword'
        })
        self.app.post('/deposit', json={'amount': 200.0})
        response = self.app.post('/withdraw', json={'amount': 50.0})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Withdrawal successful', response.data)

    def test_transfer(self):
        
        self.app.post('/signup', json={
            'email': 'transferuser@example.com',
            'username': 'transferuser',
            'password': 'securepassword'
        })

        
        response_recipient = self.app.post('/signup', json={
            'email': 'recipientuser@example.com',
            'username': 'recipientuser',
            'password': 'securepassword'
        })

        recipient_account = response_recipient.get_json().get('account_number')

        
        self.app.post('/signin', json={
            'username': 'transferuser',
            'password': 'securepassword'
        })

        
        self.app.post('/deposit', json={'amount': 200.0})

    
        response = self.app.post('/transfer', json={
            'recipient_account': recipient_account,  
            'amount': 100.0
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Transfer successful', response.data)

if __name__ == '__main__':
    unittest.main()
