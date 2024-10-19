import re
import random
from flask import Flask, redirect, request, jsonify, session, render_template, url_for
from cryptography.fernet import Fernet

app = Flask(__name__)
app.secret_key = 'supersecretkey'
users = {}
accounts = {}

key = Fernet.generate_key()
cipher_suite = Fernet(key)

existing_account_numbers = set()

class Account:
    def __init__(self, initial_balance=0):
        self.balance = initial_balance
        self.account_number = self.generate_account_number()

    @staticmethod
    def generate_account_number():
        while True:
            new_account_number = '1' + ''.join(str(random.randint(0, 9)) for _ in range(9))
            if new_account_number not in existing_account_numbers:
                existing_account_numbers.add(new_account_number)
                return new_account_number

    def deposit(self, amount):
        if amount < 0:
            return "Invalid amount. Deposit cannot be negative."
        self.balance += amount
        return f"Deposit successful. New balance: ${self.balance:.2f}"

    def withdraw(self, amount):
        if amount > self.balance:
            return "Insufficient funds. Withdrawal denied."
        self.balance -= amount
        return f"Withdrawal successful. New balance: ${self.balance:.2f}"

    def transfer(self, recipient_account_number, amount):
        if amount <= 0:
            return {"message": "Invalid amount. Transfer must be positive."}, 400

        recipient = accounts.get(recipient_account_number)
        if not recipient:
            return {"message": "Transfer failed. Recipient account not found."}, 404

        withdrawal_message = self.withdraw(amount)
        if "successful" not in withdrawal_message:
            return {"message": withdrawal_message}, 400

        recipient.deposit(amount)
        encrypted_amount = cipher_suite.encrypt(str(amount).encode()).decode()
        users[session['username']]['transactions'].append({
            'amount': encrypted_amount,
            'type': 'transfer',
            'recipient': recipient_account_number
        })

        return {
            "message": f"Transfer successful. ${amount:.2f} was transferred.",
            "new_balance": self.balance,
            "recipient_balance": recipient.balance,
            "encrypted_amount": encrypted_amount
        }, 200

    def display_balance(self):
        return f"Account Number: {self.account_number} - Current balance: ${self.balance:.2f}"

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email)

@app.route('/')
def home():
    return render_template('login.html')

@app.route("/dashboard")
def dashboard():
    if 'username' not in session:
        return redirect(url_for('home'))
    username = session['username']
    user_data = users[username]
    account_number = user_data['account_number']
    return render_template('dashboard.html', username=username, account_number=account_number)

@app.route('/signup', methods=['POST'])
def sign_up():
    data = request.json
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if any(cipher_suite.decrypt(user['email'].encode()).decode() == email for user in users.values()):
        return jsonify({"message": "Email already exists. Try a different email."}), 400

    if not is_valid_email(email):
        return jsonify({"message": "Invalid email format."}), 400

    if username in users:
        return jsonify({"message": "Username already exists. Try a different username."}), 400

    new_account = Account()
    users[username] = {
        'email': cipher_suite.encrypt(email.encode()).decode(),
        'password': cipher_suite.encrypt(password.encode()).decode(),
        'account_number': new_account.account_number,
        'transactions': []
    }
    accounts[new_account.account_number] = new_account

    return jsonify({"message": "Sign up successful", "account_number": new_account.account_number}), 201

@app.route('/signin', methods=['POST'])
def sign_in():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if username not in users:
        return jsonify({"message": "Username does not exist."}), 400

    decrypted_password = cipher_suite.decrypt(users[username]['password'].encode()).decode()
    if decrypted_password == password:
        session['username'] = username
        return jsonify({"message": "Sign in successful."}), 200
    else:
        return jsonify({"message": "Incorrect password."}), 400

@app.route('/signout', methods=['POST'])
def sign_out():
    session.pop('username', None)
    return jsonify({"message": "Sign out successful."}), 200

@app.route('/deposit', methods=['POST'])
def deposit():
    if 'username' not in session:
        return jsonify({"message": "Please sign in first."}), 401

    data = request.json
    amount = float(data.get('amount'))
    encrypted_amount = cipher_suite.encrypt(str(amount).encode()).decode()
    account = accounts[users[session['username']]['account_number']]
    message = account.deposit(amount)

    users[session['username']]['transactions'].append({
        'amount': encrypted_amount,
        'type': 'deposit'
    })

    return jsonify({"message": message}), 200

@app.route('/withdraw', methods=['POST'])
def withdraw():
    if 'username' not in session:
        return jsonify({"message": "Please sign in first."}), 401

    data = request.json
    amount = float(data.get('amount'))

    if amount <= 0:
        return jsonify({"message": "Invalid amount. Withdrawal must be positive."}), 400

    account = accounts[users[session['username']]['account_number']]
    message = account.withdraw(amount)

    if "successful" in message:
        encrypted_amount = cipher_suite.encrypt(str(amount).encode()).decode()
        users[session['username']]['transactions'].append({
            'amount': encrypted_amount,
            'type': 'withdrawal'
        })
        return jsonify({"message": message, "new_balance": account.balance, "encrypted_amount": encrypted_amount, "decrypted_amount": amount}), 200

    return jsonify({"message": message}), 400

@app.route('/transfer', methods=['POST'])
def handle_transfer():
    if 'username' not in session:
        return jsonify({"message": "Please sign in first."}), 401

    data = request.json
    recipient_account = data.get('recipient_account')
    amount = float(data.get('amount'))

    account = accounts[users[session['username']]['account_number']]
    message, status_code = account.transfer(recipient_account, amount)

    return jsonify(message), status_code

@app.route('/users', methods=['GET'])
def view_users():
    response_data = {}
    for username, data in users.items():
        decrypted_email = cipher_suite.decrypt(data['email'].encode()).decode()
        decrypted_password = cipher_suite.decrypt(data['password'].encode()).decode()
        
        deposits = []
        withdrawals = []

        for tx in data['transactions']:
            amount = cipher_suite.decrypt(tx['amount'].encode()).decode()
            if tx['type'] == 'deposit':
                deposits.append({
                    'encrypted_amount': tx['amount'],
                    'decrypted_amount': amount
                })
            elif tx['type'] == 'withdrawal':
                withdrawals.append({
                    'encrypted_amount': tx['amount'],
                    'decrypted_amount': amount
                })

        response_data[username] = {
            'email': {
                'encrypted': data['email'],
                'decrypted': decrypted_email,
            },
            'password': {
                'encrypted': data['password'],
                'decrypted': decrypted_password,
            },
            'account_number': data['account_number'],
            'deposits': deposits,
            'withdrawals': withdrawals
        }
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True)
