import os
from datetime import timedelta

from flask import Flask, jsonify, request, render_template, send_from_directory, session

import db

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=90)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True

db.init_db()

OPEN_PATHS = {'/', '/manifest.json', '/api/login', '/api/signup'}


@app.before_request
def require_login():
    if request.path in OPEN_PATHS or request.path.startswith('/static/'):
        return
    if 'account_id' not in session:
        return jsonify({'error': 'unauthorized'}), 401


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')


@app.route('/api/signup', methods=['POST'])
def signup():
    body = request.get_json(force=True)
    if body.get('inviteCode', '') != os.environ['SIGNUP_CODE']:
        return jsonify({'error': 'invalid invite code'}), 403
    username = body.get('username', '').strip()
    password = body.get('password', '')
    teacher_name = body.get('teacherName', '').strip()
    if not username or not password:
        return jsonify({'error': 'username and password are required'}), 400
    account_id = db.create_account(username, password, teacher_name)
    if account_id is None:
        return jsonify({'error': 'username already taken'}), 409
    session.permanent = True
    session['account_id'] = account_id
    return jsonify({'teacherName': teacher_name})


@app.route('/api/login', methods=['POST'])
def login():
    body = request.get_json(force=True)
    account = db.verify_login(body.get('username', ''), body.get('password', ''))
    if not account:
        return jsonify({'error': 'invalid credentials'}), 401
    session.permanent = True
    session['account_id'] = account['id']
    return jsonify({'teacherName': account['teacher_name']})


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'ok': True})


@app.route('/api/me', methods=['GET'])
def me():
    account = db.get_account(session['account_id'])
    return jsonify(account)


@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(db.get_state(session['account_id']))


@app.route('/api/state/<key>', methods=['PUT'])
def put_state(key):
    if key not in ('students', 'settings'):
        return jsonify({'error': 'invalid key'}), 400
    body = request.get_json(force=True)
    db.set_kv(session['account_id'], key, body['value'])
    return jsonify({'ok': True})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
