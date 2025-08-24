from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, current_app, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from app.models.user import Customer, BookingAgent, AirlineStaff
from app.models.flight import Airline
from app.models import db

import hashlib

auth = Blueprint('auth', __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please login first.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)

    return decorated_function


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        username = request.form.get('username')
        password = request.form.get('password')

        # Hash password using MD5 as per project requirements
        hashed_password = hashlib.md5(password.encode()).hexdigest()

        if user_type == 'customer':
            user = Customer.query.filter_by(email=username).first()
            if user and user.password == hashed_password:
                session['user'] = user.email
                session['user_type'] = 'customer'
                flash('Welcome back!', 'success')
                return redirect(url_for('public.index'))

        elif user_type == 'agent':
            user = BookingAgent.query.filter_by(email=username).first()
            if user and user.password == hashed_password:
                session['user'] = user.email
                session['user_type'] = 'agent'
                session['agent_id'] = user.booking_agent_id
                flash('Welcome back!', 'success')
                return redirect(url_for('public.index'))
        elif user_type == 'staff':

            user = AirlineStaff.query.filter_by(username=username).first()

            if user and user.password == hashed_password:
                if not user.approved:
                    flash('Your account is pending approval. Please contact admin.', 'warning')
                    return redirect(url_for('auth.login'))
                session['user'] = user.username
                session['user_type'] = 'staff'
                session['airline_name'] = user.airline_name  # 确保这里使用 airline_name
                print("生成的URL:", url_for('staff.dashboard'))  # 添加这行
                flash('Welcome back!', 'success')
                return redirect(url_for('public.index'))
        flash('Invalid username or password.', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('auth/login.html')


@auth.route('/register', methods=['GET'])
def register():
    return render_template('auth/register.html')


@auth.route('/register/customer', methods=['POST'])
def register_customer():
    try:
        # Get form data
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        building = request.form.get('building')
        street = request.form.get('street')
        city = request.form.get('city')
        state = request.form.get('state')
        phone = request.form.get('phone')
        passport = request.form.get('passport')
        passport_exp = request.form.get('passport_exp')
        passport_country = request.form.get('passport_country')
        dob = request.form.get('dob')

        # Check if user already exists
        if Customer.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))

        # Create new customer
        new_customer = Customer(
            email=email,
            name=name,
            password=hashlib.md5(password.encode()).hexdigest(),
            building_number=building,
            street=street,
            city=city,
            state=state,
            phone_number=phone,
            passport_number=passport,
            passport_expiration=passport_exp,
            passport_country=passport_country,
            date_of_birth=dob
        )

        db.session.add(new_customer)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))

    except Exception as e:
        db.session.rollback()
        flash('Registration failed. Please try again.', 'danger')
        return redirect(url_for('auth.register'))


@auth.route('/register/agent', methods=['POST'])
def register_agent():
    try:
        # 获取表单数据
        email = request.form.get('email')
        password = request.form.get('password')
        booking_agent_id = request.form.get('booking_agent_id')

        # 检查 email 是否已注册
        if not email or not password or not booking_agent_id:
            flash('All fields are required.', 'danger')
            return redirect(url_for('auth.register'))

        if BookingAgent.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))

        # 检查 booking_agent_id 是否唯一（可选）
        if BookingAgent.query.filter_by(booking_agent_id=booking_agent_id).first():
            flash('Booking agent ID already exists.', 'danger')
            return redirect(url_for('auth.register'))

        # 创建新的代理账户
        new_agent = BookingAgent(
            email=email,
            password=hashlib.md5(password.encode()).hexdigest(),
            booking_agent_id=booking_agent_id,
            approved=False  # 默认未审批
        )

        db.session.add(new_agent)
        db.session.commit()

        flash('Registration successful! Please wait for airline staff to approve your account.', 'info')
        return redirect(url_for('auth.login'))

    except Exception as e:
        db.session.rollback()
        flash(f'Registration failed. Error: {str(e)}', 'danger')
        return redirect(url_for('auth.register'))



@auth.route('/register/staff', methods=['POST'])
def register_staff():
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        date_of_birth = request.form.get('date_of_birth')
        airline_name = request.form.get('airline_name')

        # 检查用户名是否已存在
        if AirlineStaff.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return redirect(url_for('auth.register'))

        # 检查航空公司是否存在
        if not Airline.query.filter_by(airline_name=airline_name).first():
            flash('Invalid airline name.', 'danger')
            return redirect(url_for('auth.register'))

        # 创建新员工
        new_staff = AirlineStaff(
            username=username,
            password=hashlib.md5(password.encode()).hexdigest(),
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            airline_name=airline_name,
        )
        db.session.add(new_staff)
        db.session.commit()

        # 检查是否需要赋予 Admin 权限
        connection = current_app.config['GET_DB']()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM permission 
            JOIN airline_staff ON permission.username = airline_staff.username
            WHERE permission_type = 'Admin' AND airline_name = %s
        """, (airline_name,))
        has_admin = cursor.fetchone()[0]

        if has_admin == 0:
            cursor.execute("""
                INSERT INTO permission (username, permission_type)
                VALUES (%s, 'Admin')
            """, (username,))
            connection.commit()
            flash('You have been granted Admin permissions as the first staff member.', 'info')

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))

    except Exception as e:
        db.session.rollback()
        flash('Wait for your Admin to approve', 'success')
        return redirect(url_for('auth.register'))


@auth.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('public.index'))