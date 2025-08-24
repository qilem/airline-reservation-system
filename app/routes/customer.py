from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, current_app, flash
from datetime import datetime, timedelta
from functools import wraps
from app.models import db

customer = Blueprint('customer', __name__)


def customer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session or session['user_type'] != 'customer':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)

    return decorated_function


@customer.route('/home', methods=['GET'], endpoint='dashboard')
@customer_required
def home():
    """Customer homepage showing upcoming flights"""
    connection = current_app.config['GET_DB']()  # 获取 pymysql 数据库连接
    cursor = connection.cursor()

    query = """
        SELECT f.* 
        FROM flight f
        JOIN ticket t ON f.airline_name = t.airline_name AND f.flight_num = t.flight_num
        JOIN purchases p ON t.ticket_id = p.ticket_id
        WHERE p.customer_email = %s AND f.departure_time > NOW()
        ORDER BY f.departure_time
    """
    cursor.execute(query, (session['user'],))
    upcoming_flights = cursor.fetchall()
    cursor.close()
    connection.close()  # 关闭连接

    return render_template('customer/dashboard.html', flights=upcoming_flights)



@customer.route('/my_flights', methods=['GET'], endpoint='my_flights')
@customer_required
def my_flights():
    """View customer's flight history"""
    # 使用原生 pymysql 连接
    connection = current_app.config['GET_DB']()
    cursor = connection.cursor()

    query = """
        SELECT f.* 
        FROM flight f
        JOIN ticket t ON f.airline_name = t.airline_name AND f.flight_num = t.flight_num
        JOIN purchases p ON t.ticket_id = p.ticket_id
        WHERE p.customer_email = %s
        ORDER BY f.departure_time DESC
    """
    cursor.execute(query, (session['user'],))
    flights = cursor.fetchall()

    # 关闭游标和连接
    cursor.close()
    connection.close()

    return render_template('customer/view_flights.html', flights=flights)


@customer.route('/purchase/<int:flight_num>/<airline_name>', methods=['GET', 'POST'])
@customer_required
def purchase_ticket(flight_num, airline_name):
    connection = current_app.config['GET_DB']()
    cursor = connection.cursor()

    try:
        if request.method == 'POST':
            # Check if flight exists
            cursor.execute("""
                SELECT * FROM flight 
                WHERE airline_name = %s AND flight_num = %s
            """, (airline_name, flight_num))
            flight = cursor.fetchone()

            if not flight:
                flash("Flight does not exist.", "danger")
                return redirect(url_for('customer.search_flights'))

            # Check available seats
            cursor.execute("""
                SELECT (a.seats - COUNT(t.ticket_id)) as available_seats
                FROM flight f 
                JOIN airplane a ON f.airline_name = a.airline_name 
                    AND f.airplane_id = a.airplane_id
                LEFT JOIN ticket t ON f.airline_name = t.airline_name 
                    AND f.flight_num = t.flight_num
                WHERE f.airline_name = %s AND f.flight_num = %s
                GROUP BY a.seats
            """, (airline_name, flight_num))

            result = cursor.fetchone()
            if not result or result['available_seats'] <= 0:
                flash("Sorry, this flight is fully booked.", "danger")
                return redirect(url_for('customer.search_flights'))

            # Get next ticket_id
            cursor.execute("SELECT MAX(ticket_id) as max_id FROM ticket")
            result = cursor.fetchone()
            next_ticket_id = 1 if result['max_id'] is None else result['max_id'] + 1

            # Create ticket record
            cursor.execute("""
                INSERT INTO ticket (ticket_id, airline_name, flight_num)
                VALUES (%s, %s, %s)
            """, (next_ticket_id, airline_name, flight_num))
            connection.commit()

            # Create purchase record
            cursor.execute("""
                INSERT INTO purchases (ticket_id, customer_email, purchase_date)
                VALUES (%s, %s, CURDATE())
            """, (next_ticket_id, session['user']))
            connection.commit()

            flash("Ticket purchased successfully!", "success")
            return redirect(url_for('customer.my_flights'))

        # GET request handling
        cursor.execute("""
            SELECT f.*, 
                   (a.seats - COUNT(t.ticket_id)) as available_seats
            FROM flight f
            JOIN airplane a ON f.airline_name = a.airline_name 
                AND f.airplane_id = a.airplane_id
            LEFT JOIN ticket t ON f.airline_name = t.airline_name 
                AND f.flight_num = t.flight_num
            WHERE f.airline_name = %s AND f.flight_num = %s
            GROUP BY f.airline_name, f.flight_num, a.seats
        """, (airline_name, flight_num))
        flight = cursor.fetchone()

        if not flight:
            flash("Flight not found", "danger")
            return redirect(url_for('customer.search_flights'))

        return render_template('customer/purchase.html', flight=flight)

    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        connection.rollback()
        return redirect(url_for('customer.search_flights'))
    finally:
        cursor.close()
        connection.close()


@customer.route('/spending', methods=['GET', 'POST'], endpoint='spending')
@customer_required
def track_spending():
    connection = current_app.config['GET_DB']()
    cursor = connection.cursor()

    try:
        if request.method == 'POST':
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')

            # 确保日期字符串正确转换为日期对象
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            else:
                start_date = datetime.now().date() - timedelta(days=365)

            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            else:
                end_date = datetime.now().date()
        else:
            # 默认时间范围为过去一年
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=365)

        # 查询用户消费记录
        query = """
    SELECT DATE_FORMAT(p.purchase_date, '%%Y-%%m') as month, 
           SUM(f.price) as total
    FROM purchases p
    JOIN ticket t ON p.ticket_id = t.ticket_id
    JOIN flight f ON t.airline_name = f.airline_name AND t.flight_num = f.flight_num
    WHERE p.customer_email = %s AND p.purchase_date BETWEEN %s AND %s
    GROUP BY DATE_FORMAT(p.purchase_date, '%%Y-%%m')
    ORDER BY month ASC
"""

        cursor.execute(query, (session['user'], start_date, end_date))
        spending_data = cursor.fetchall()

        # 确保 `spending_data` 中有内容
        months = [row['month'] for row in spending_data]
        totals = [float(row['total']) for row in spending_data]
        total_spending = sum(row['total'] for row in spending_data if row['total'] is not None)
        return render_template('customer/track_spending.html',
                               spending_data=spending_data,
                               total_spending=total_spending,
                               months=months,
                               totals=totals,
                               start_date=start_date,
                               end_date=end_date)
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('customer.dashboard'))
    finally:
        cursor.close()
        connection.close()

