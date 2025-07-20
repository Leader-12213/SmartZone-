
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import json
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import random

app = Flask(__name__)
app.secret_key = 'smart_zone_secret_key_2024'

# Data files
USERS_FILE = 'users.json'
DEPOSITS_FILE = 'deposits.json'
WITHDRAWALS_FILE = 'withdrawals.json'
TRANSACTIONS_FILE = 'transactions.json'
DAILY_LIMITS_FILE = 'daily_limits.json'
VIP1_DRAW_FILE = 'vip1_draw.json'

def load_json_file(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_json_file(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user_by_id(user_id):
    users = load_json_file(USERS_FILE)
    return next((user for user in users if user['id'] == user_id), None)

def get_user_by_phone(phone):
    users = load_json_file(USERS_FILE)
    return next((user for user in users if user['phone'] == phone), None)

def generate_user_id():
    users = load_json_file(USERS_FILE)
    if not users:
        return "SZ001"
    last_id = max([int(user['id'][2:]) for user in users])
    return f"SZ{str(last_id + 1).zfill(3)}"

def generate_invite_code():
    return str(uuid.uuid4())[:8].upper()

def get_today_date():
    return datetime.now().strftime('%Y-%m-%d')

def get_daily_limits():
    daily_limits = load_json_file(DAILY_LIMITS_FILE)
    today = get_today_date()
    
    # إذا لم يوجد سجل لليوم الحالي، أنشئ واحداً جديداً
    if not daily_limits or daily_limits.get('date') != today:
        daily_limits = {
            'date': today,
            'vip1_sold': 0,
            'vip2_sold': 0,
            'vip3_sold': 0
        }
        save_json_file(DAILY_LIMITS_FILE, daily_limits)
    
    return daily_limits

def update_daily_limits(product_type):
    daily_limits = get_daily_limits()
    if product_type == 'vip1':
        daily_limits['vip1_sold'] += 1
    elif product_type == 'vip2':
        daily_limits['vip2_sold'] += 1
    elif product_type == 'vip3':
        daily_limits['vip3_sold'] += 1
    
    save_json_file(DAILY_LIMITS_FILE, daily_limits)
    return daily_limits

def generate_draw_code():
    return ''.join([str(random.randint(0, 9)) for _ in range(10)])

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    return render_template('home.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'login':
            identifier = request.form.get('identifier')
            password = request.form.get('password')
            
            user = get_user_by_phone(identifier) or get_user_by_id(identifier)
            
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('index'))
            else:
                flash('بيانات الدخول غير صحيحة')
        
        elif action == 'register':
            username = request.form.get('username')
            phone = request.form.get('phone')
            password = request.form.get('password')
            invite_code = request.form.get('invite_code')
            
            users = load_json_file(USERS_FILE)
            
            # Check if first user
            if users and not invite_code:
                flash('رمز الدعوة مطلوب')
                return render_template('login.html')
            
            if users and invite_code:
                inviter = next((user for user in users if user['invite_code'] == invite_code), None)
                if not inviter:
                    flash('رمز الدعوة غير صحيح')
                    return render_template('login.html')
            
            if get_user_by_phone(phone):
                flash('رقم الهاتف مسجل مسبقاً')
                return render_template('login.html')
            
            user_id = generate_user_id()
            new_user = {
                'id': user_id,
                'username': username,
                'phone': phone,
                'password': generate_password_hash(password),
                'invite_code': generate_invite_code(),
                'invited_by': invite_code if users else None,
                'egp_balance': 0,
                'usdt_balance': 0,
                'created_at': datetime.now().isoformat(),
                'team_members': []
            }
            
            users.append(new_user)
            save_json_file(USERS_FILE, users)
            
            # Add to inviter's team
            if users and invite_code:
                for user in users:
                    if user['invite_code'] == invite_code:
                        user['team_members'].append(user_id)
                        break
                save_json_file(USERS_FILE, users)
            
            session['user_id'] = user_id
            session['username'] = username
            return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/products')
def products():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    daily_limits = get_daily_limits()
    limits_info = {
        'vip1': {'sold': daily_limits['vip1_sold'], 'max': 25},
        'vip2': {'sold': daily_limits['vip2_sold'], 'max': 10},
        'vip3': {'sold': daily_limits['vip3_sold'], 'max': 100}  # بدون حد أقصى فعلي
    }
    
    return render_template('products.html', limits=limits_info)

@app.route('/my_products')
def my_products():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    transactions = load_json_file(TRANSACTIONS_FILE)
    user_products = []
    
    for transaction in transactions:
        if (transaction['user_id'] == session['user_id'] and 
            transaction['type'] == 'شراء منتج'):
            user_products.append(transaction)
    
    return render_template('my_products.html', user_products=user_products)

@app.route('/buy_product', methods=['POST'])
def buy_product():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'يجب تسجيل الدخول أولاً'})
    
    data = request.get_json()
    product_type = data.get('product')
    
    # تحديد تفاصيل المنتج
    products = {
        'vip1': {'price': 200, 'daily_income': 40, 'duration': 10, 'max_daily': 25},
        'vip2': {'price': 500, 'daily_income': 100, 'duration': 10, 'max_daily': 10},
        'vip3': {'price': 1000, 'daily_income': 230, 'duration': 10, 'max_daily': 999}
    }
    
    if product_type not in products:
        return jsonify({'success': False, 'message': 'منتج غير صحيح'})
    
    # التحقق من الحد الأقصى اليومي
    daily_limits = get_daily_limits()
    product_sold_key = f'{product_type}_sold'
    
    if daily_limits.get(product_sold_key, 0) >= products[product_type]['max_daily']:
        return jsonify({'success': False, 'message': 'تم الوصول للحد الأقصى اليومي، يرجى المحاولة غداً'})
    
    product = products[product_type]
    user = get_user_by_id(session['user_id'])
    
    # التحقق من الرصيد
    if user['egp_balance'] < product['price']:
        return jsonify({'success': False, 'message': 'الرصيد غير كافي'})
    
    # خصم المبلغ من الرصيد
    users = load_json_file(USERS_FILE)
    for u in users:
        if u['id'] == session['user_id']:
            u['egp_balance'] -= product['price']
            break
    save_json_file(USERS_FILE, users)
    
    # تحديث الحد اليومي
    update_daily_limits(product_type)
    
    # إضافة عملية الشراء للمعاملات
    transactions = load_json_file(TRANSACTIONS_FILE)
    purchase_time = datetime.now()
    
    transactions.append({
        'id': str(uuid.uuid4()),
        'user_id': session['user_id'],
        'type': 'شراء منتج',
        'product': product_type.upper(),
        'amount': product['price'],
        'currency': 'EGP',
        'status': 'مكتملة',
        'created_at': purchase_time.isoformat(),
        'next_profit_time': (purchase_time + timedelta(hours=25)).isoformat(),
        'daily_income': product['daily_income'],
        'remaining_days': product['duration']
    })
    save_json_file(TRANSACTIONS_FILE, transactions)
    
    return jsonify({'success': True, 'message': f'تم شراء {product_type.upper()} بنجاح!'})

@app.route('/process_daily_profits')
def process_daily_profits():
    """معالجة الأرباح اليومية - يتم تشغيلها تلقائياً"""
    users = load_json_file(USERS_FILE)
    transactions = load_json_file(TRANSACTIONS_FILE)
    
    current_time = datetime.now()
    
    for transaction in transactions:
        if (transaction['type'] == 'شراء منتج' and 
            transaction.get('remaining_days', 0) > 0 and
            transaction.get('next_profit_time')):
            
            next_profit_time = datetime.fromisoformat(transaction['next_profit_time'])
            
            if current_time >= next_profit_time:
                # إضافة الربح للمستخدم
                for user in users:
                    if user['id'] == transaction['user_id']:
                        user['egp_balance'] += transaction['daily_income']
                        break
                
                # تحديث المعاملة
                transaction['remaining_days'] -= 1
                if transaction['remaining_days'] > 0:
                    transaction['next_profit_time'] = (current_time + timedelta(hours=25)).isoformat()
                else:
                    transaction['next_profit_time'] = None
                
                # إضافة معاملة الربح
                transactions.append({
                    'id': str(uuid.uuid4()),
                    'user_id': transaction['user_id'],
                    'type': 'ربح يومي',
                    'product': transaction.get('product', ''),
                    'amount': transaction['daily_income'],
                    'currency': 'EGP',
                    'status': 'مكتملة',
                    'created_at': current_time.isoformat()
                })
    
    save_json_file(USERS_FILE, users)
    save_json_file(TRANSACTIONS_FILE, transactions)
    
    return jsonify({'message': 'تم معالجة الأرباح اليومية'})

@app.route('/check_profits')
def check_profits():
    """فحص وتحديث الأرباح - يمكن استدعاؤها من الواجهة"""
    process_daily_profits()
    return redirect(url_for('profile'))

@app.route('/team')
def team():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user = get_user_by_id(session['user_id'])
    users = load_json_file(USERS_FILE)
    
    team_data = []
    for member_id in current_user.get('team_members', []):
        member = get_user_by_id(member_id)
        if member:
            team_data.append({
                'id': member['id'],
                'username': member['username']
            })
    
    return render_template('team.html', team_members=team_data, user=current_user)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    transactions = load_json_file(TRANSACTIONS_FILE)
    user_transactions = [t for t in transactions if t['user_id'] == session['user_id']]
    
    return render_template('profile.html', user=user, transactions=user_transactions)

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        currency = request.form.get('currency')
        user_id = request.form.get('user_id')
        amount = float(request.form.get('amount', 0))
        
        deposits = load_json_file(DEPOSITS_FILE)
        
        deposit_data = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'currency': currency,
            'amount': amount,
            'status': 'قيد المراجعة',
            'created_at': datetime.now().isoformat()
        }
        
        if currency == 'EGP':
            deposit_data['phone'] = request.form.get('phone')
            deposit_data['receiver_phone'] = '010XXXXXXXX'
        else:  # USDT
            deposit_data['sender_address'] = request.form.get('sender_address')
            deposit_data['receiver_address'] = '0x3e7f071632EEcAAcA2BCB6fC235B9b3a70Db7191'
        
        deposits.append(deposit_data)
        save_json_file(DEPOSITS_FILE, deposits)
        
        # Add to transactions
        transactions = load_json_file(TRANSACTIONS_FILE)
        transactions.append({
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'type': 'إيداع',
            'amount': amount,
            'currency': currency,
            'status': 'قيد المراجعة',
            'created_at': datetime.now().isoformat()
        })
        save_json_file(TRANSACTIONS_FILE, transactions)
        
        flash('تم إرسال طلب الإيداع بنجاح')
        return redirect(url_for('profile'))
    
    return render_template('deposit.html')

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        currency = request.form.get('currency')
        amount = float(request.form.get('amount', 0))
        
        user = get_user_by_id(session['user_id'])
        
        # Check balance
        current_balance = user['egp_balance'] if currency == 'EGP' else user['usdt_balance']
        withdrawal_fee = amount * 0.25  # 25% fee
        total_deduction = amount + withdrawal_fee
        
        if current_balance < total_deduction:
            flash('الرصيد غير كافي')
            return redirect(url_for('withdraw'))
        
        withdrawals = load_json_file(WITHDRAWALS_FILE)
        
        withdrawal_data = {
            'id': str(uuid.uuid4()),
            'user_id': session['user_id'],
            'currency': currency,
            'amount': amount,
            'fee': withdrawal_fee,
            'total_deduction': total_deduction,
            'status': 'قيد المراجعة',
            'created_at': datetime.now().isoformat()
        }
        
        if currency == 'EGP':
            withdrawal_data['phone'] = request.form.get('phone')
        else:  # USDT
            withdrawal_data['address'] = request.form.get('address')
        
        withdrawals.append(withdrawal_data)
        save_json_file(WITHDRAWALS_FILE, withdrawals)
        
        # Add to transactions
        transactions = load_json_file(TRANSACTIONS_FILE)
        transactions.append({
            'id': str(uuid.uuid4()),
            'user_id': session['user_id'],
            'type': 'سحب',
            'amount': amount,
            'currency': currency,
            'status': 'قيد المراجعة',
            'created_at': datetime.now().isoformat()
        })
        save_json_file(TRANSACTIONS_FILE, transactions)
        
        flash('تم إرسال طلب السحب بنجاح')
        return redirect(url_for('profile'))
    
    user = get_user_by_id(session['user_id'])
    return render_template('withdraw.html', user=user)

@app.route('/join_vip1_draw', methods=['POST'])
def join_vip1_draw():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'يجب تسجيل الدخول أولاً'})
    
    user = get_user_by_id(session['user_id'])
    
    # التحقق من الرصيد
    if user['egp_balance'] < 10:
        return jsonify({'success': False, 'message': 'الرصيد غير كافي. يحتاج 10 EGP للانضمام'})
    
    # خصم المبلغ من الرصيد
    users = load_json_file(USERS_FILE)
    for u in users:
        if u['id'] == session['user_id']:
            u['egp_balance'] -= 10
            break
    save_json_file(USERS_FILE, users)
    
    # توليد كود السحب
    draw_code = generate_draw_code()
    
    # حفظ بيانات السحب
    vip1_draws = load_json_file(VIP1_DRAW_FILE)
    draw_entry = {
        'user_id': session['user_id'],
        'draw_code': draw_code,
        'join_date': datetime.now().isoformat()
    }
    vip1_draws.append(draw_entry)
    save_json_file(VIP1_DRAW_FILE, vip1_draws)
    
    # إضافة معاملة
    transactions = load_json_file(TRANSACTIONS_FILE)
    transactions.append({
        'id': str(uuid.uuid4()),
        'user_id': session['user_id'],
        'type': 'انضمام سحب VIP1',
        'amount': 10,
        'currency': 'EGP',
        'status': 'مكتملة',
        'created_at': datetime.now().isoformat(),
        'draw_code': draw_code
    })
    save_json_file(TRANSACTIONS_FILE, transactions)
    
    return jsonify({
        'success': True, 
        'message': f'تم الانضمام بنجاح! كود السحب: {draw_code}',
        'draw_code': draw_code
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
