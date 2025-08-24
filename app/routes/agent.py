from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, current_app, flash
from datetime import datetime, timedelta
from functools import wraps
from app.models import db

agent = Blueprint('agent', __name__)

def agent_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session or session['user_type'] != 'agent':
            return redirect(url_for('auth.login'))

        # 检查用户是否已被批准
        connection = current_app.config['GET_DB']()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT approved 
                FROM booking_agent 
                WHERE email = %s
            """, (session['user'],))  # 假设 session['user'] 是代理用户的 email
            result = cursor.fetchone()
            if not result or not result['approved']:
                flash('Your account is pending approval. Please contact airline staff.', 'danger')
                return redirect(url_for('auth.login'))
        finally:
            cursor.close()
            connection.close()

        return f(*args, **kwargs)

    return decorated_function



@agent.route('/dashboard')  # Changed from /home to /dashboard
@agent_required
def dashboard():
    """Agent dashboard showing summary and recent bookings"""
    connection = current_app.config['GET_DB']()
    cursor = connection.cursor()  # No need for 'dictionary=True'

    try:
        # Get 30-day summary data
        summary_query = """
            SELECT 
                COUNT(*) as tickets_sold,
                SUM(f.price * 0.1) as total_commission,
                SUM(f.price * 0.1)/COUNT(*) as avg_commission
            FROM purchases p
            JOIN ticket t ON p.ticket_id = t.ticket_id
            JOIN flight f ON t.airline_name = f.airline_name AND t.flight_num = f.flight_num
            WHERE p.booking_agent_id = %s 
            AND p.purchase_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """
        cursor.execute(summary_query, (session['agent_id'],))
        summary = cursor.fetchone()

        # Get recent bookings
        bookings_query = """
            SELECT 
                f.flight_num, f.airline_name, f.departure_airport,
                f.arrival_airport, f.departure_time, f.status,
                c.name as customer_name, c.email as customer_email,
                p.purchase_date, f.price
            FROM flight f
            JOIN ticket t ON f.airline_name = t.airline_name AND f.flight_num = t.flight_num
            JOIN purchases p ON t.ticket_id = p.ticket_id
            JOIN customer c ON p.customer_email = c.email
            WHERE p.booking_agent_id = %s AND f.departure_time > NOW()
            ORDER BY p.purchase_date DESC LIMIT 5
        """
        cursor.execute(bookings_query, (session['agent_id'],))
        recent_bookings = cursor.fetchall()

        # Get top customer
        top_customer_query = """
            SELECT c.name, COUNT(*) as tickets
            FROM purchases p
            JOIN customer c ON p.customer_email = c.email
            WHERE p.booking_agent_id = %s 
            AND p.purchase_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY c.email, c.name
            ORDER BY tickets DESC
            LIMIT 1
        """
        cursor.execute(top_customer_query, (session['agent_id'],))
        top_customer = cursor.fetchone()

    finally:
        cursor.close()
        connection.close()

    return render_template('agent/dashboard.html',
                           total_commission=summary['total_commission'] or 0,
                           avg_commission=summary['avg_commission'] or 0,
                           tickets_sold=summary['tickets_sold'] or 0,
                           bookings=recent_bookings,
                           top_customer=top_customer or {'name': 'No data', 'tickets': 0})


@agent.route('/flights', endpoint='my_flights')
@agent_required
def view_flights():
    db = current_app.config['GET_DB']()
    cursor = db.cursor()

    try:
        # Get filter parameters
        source = request.args.get('source', '')
        destination = request.args.get('destination', '')
        start_date = request.args.get('start_date', datetime.now().strftime('%Y-%m-%d'))
        end_date = request.args.get('end_date', '')

        query = """
            SELECT DISTINCT
                f.airline_name,
                f.flight_num,
                f.departure_airport,
                dep.airport_city as departure_city,
                f.departure_time,
                f.arrival_airport,
                arr.airport_city as arrival_city,
                f.arrival_time,
                f.price,
                f.status,
                c.name as customer_name,
                c.email as customer_email,
                p.purchase_date
            FROM flight f
            JOIN airport dep ON f.departure_airport = dep.airport_name
            JOIN airport arr ON f.arrival_airport = arr.airport_name
            JOIN ticket t ON f.airline_name = t.airline_name AND f.flight_num = t.flight_num
            JOIN purchases p ON t.ticket_id = p.ticket_id
            JOIN customer c ON p.customer_email = c.email
            WHERE p.booking_agent_id = %s
        """
        params = [session['agent_id']]

        if source:
            query += " AND (dep.airport_name LIKE %s OR dep.airport_city LIKE %s)"
            params.extend(['%' + source + '%', '%' + source + '%'])

        if destination:
            query += " AND (arr.airport_name LIKE %s OR arr.airport_city LIKE %s)"
            params.extend(['%' + destination + '%', '%' + destination + '%'])

        if start_date:
            query += " AND f.departure_time >= %s"
            params.append(start_date)

        if end_date:
            query += " AND f.departure_time <= %s"
            params.append(end_date)

        query += " ORDER BY f.departure_time ASC"

        cursor.execute(query, tuple(params))
        flights = cursor.fetchall()

        return render_template('agent/my_flights.html',
                               flights=flights,
                               source=source,
                               destination=destination,
                               start_date=start_date,
                               end_date=end_date)
    finally:
        cursor.close()
        db.close()



@agent.route('/commission', endpoint='commission')
@agent_required
def view_commission():
    """View agent's commission with date range filtering"""
    connection = current_app.config['GET_DB']()
    cursor = connection.cursor()  # No need for 'dictionary=True'

    # Get date range parameters
    start_date = request.args.get('start_date',
                                  (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date',
                                datetime.now().strftime('%Y-%m-%d'))

    # Get summary data for date range
    summary_query = """
        SELECT 
            SUM(f.price * 0.1) as total_commission,
            COUNT(*) as tickets_count,
            AVG(f.price * 0.1) as avg_commission
        FROM purchases p
        JOIN ticket t ON p.ticket_id = t.ticket_id
        JOIN flight f ON t.airline_name = f.airline_name AND t.flight_num = f.flight_num
        WHERE p.booking_agent_id = %s 
        AND p.purchase_date BETWEEN %s AND %s
    """
    cursor.execute(summary_query, (session['agent_id'], start_date, end_date))
    summary = cursor.fetchone()

    # Get daily commission data for chart
    daily_query = """
        SELECT 
            DATE(p.purchase_date) as date,
            SUM(f.price * 0.1) as commission
        FROM purchases p
        JOIN ticket t ON p.ticket_id = t.ticket_id
        JOIN flight f ON t.airline_name = f.airline_name AND t.flight_num = f.flight_num
        WHERE p.booking_agent_id = %s 
        AND p.purchase_date BETWEEN %s AND %s
        GROUP BY DATE(p.purchase_date)
        ORDER BY date
    """
    cursor.execute(daily_query, (session['agent_id'], start_date, end_date))
    daily_data = cursor.fetchall()

    cursor.close()

    # Prepare chart data
    dates = [row['date'].strftime('%Y-%m-%d') for row in daily_data]
    daily_commission = [float(row['commission']) for row in daily_data]

    return render_template('agent/commission.html',
                           start_date=start_date,
                           end_date=end_date,
                           total_commission=summary['total_commission'] or 0,
                           avg_commission=summary['avg_commission'] or 0,
                           tickets_count=summary['tickets_count'] or 0,
                           dates=dates,
                           daily_commission=daily_commission)


@agent.route('/top_customers', endpoint='top_customers')
@agent_required
def view_top_customers():
    """View top customers by tickets and commission"""
    connection = current_app.config['GET_DB']()
    cursor = connection.cursor()  # No need for 'dictionary=True'

    # Top 5 by tickets (6 months)
    tickets_query = """
        SELECT 
            c.email, c.name,
            COUNT(*) as tickets
        FROM purchases p
        JOIN customer c ON p.customer_email = c.email
        WHERE p.booking_agent_id = %s 
        AND p.purchase_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY c.email, c.name
        ORDER BY tickets DESC
        LIMIT 5
    """

    # Top 5 by commission (1 year)
    commission_query = """
        SELECT 
            c.email, c.name,
            SUM(f.price * 0.1) as commission
        FROM purchases p
        JOIN customer c ON p.customer_email = c.email
        JOIN ticket t ON p.ticket_id = t.ticket_id
        JOIN flight f ON t.airline_name = f.airline_name AND t.flight_num = f.flight_num
        WHERE p.booking_agent_id = %s 
        AND p.purchase_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
        GROUP BY c.email, c.name
        ORDER BY commission DESC
        LIMIT 5
    """

    cursor.execute(tickets_query, (session['agent_id'],))
    top_by_tickets = cursor.fetchall()

    cursor.execute(commission_query, (session['agent_id'],))
    top_by_commission = cursor.fetchall()

    cursor.close()

    # Prepare chart data
    ticket_customers = [customer['name'] for customer in top_by_tickets]
    ticket_counts = [customer['tickets'] for customer in top_by_tickets]
    commission_customers = [customer['name'] for customer in top_by_commission]
    commission_amounts = [float(customer['commission']) for customer in top_by_commission]

    return render_template('agent/top_customers.html',
                           top_by_tickets=top_by_tickets,
                           top_by_commission=top_by_commission,
                           ticket_customers=ticket_customers,
                           ticket_counts=ticket_counts,
                           commission_customers=commission_customers,
                           commission_amounts=commission_amounts)

@agent.route('/search_flights', endpoint='search_flights')
@agent_required
def search_flights():
    """Search flights for agents based on filters"""
    connection = current_app.config['GET_DB']()
    cursor = connection.cursor()

    # 获取搜索参数
    departure_airport = request.args.get('departure_airport', '')
    arrival_airport = request.args.get('arrival_airport', '')
    start_date = request.args.get('start_date', (datetime.now()).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'))

    # 搜索航班的 SQL 查询
    query = """
        SELECT 
            flight.flight_num,
            flight.airline_name,
            flight.departure_airport,
            flight.arrival_airport,
            flight.departure_time,
            flight.arrival_time,
            flight.status,
            flight.price
        FROM flight
        WHERE 
            flight.departure_airport LIKE %s AND
            flight.arrival_airport LIKE %s AND
            flight.departure_time BETWEEN %s AND %s
        ORDER BY flight.departure_time ASC
    """
    cursor.execute(query, (
        f"%{departure_airport}%",
        f"%{arrival_airport}%",
        start_date,
        end_date
    ))
    flights = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('agent/search_flights.html',
                           flights=flights,
                           departure_airport=departure_airport,
                           arrival_airport=arrival_airport,
                           start_date=start_date,
                           end_date=end_date)

@agent.route('/book_ticket_for_customer', methods=['GET', 'POST'])
@agent_required
def book_ticket_for_customer():
    connection = current_app.config['GET_DB']()
    cursor = connection.cursor()

    try:
        flight_num = request.args.get('flight_num')
        airline_name = request.args.get('airline_name')

        if request.method == 'POST':
            customer_email = request.form.get('customer_email')

            # 检查客户是否存在
            cursor.execute("""
                SELECT email FROM customer WHERE email = %s
            """, (customer_email,))
            customer = cursor.fetchone()

            if not customer:
                flash("Customer email does not exist.", "danger")
                return redirect(url_for('agent.search_flights'))

            # 检查航班是否存在
            cursor.execute("""
                SELECT * FROM flight 
                WHERE airline_name = %s AND flight_num = %s
            """, (airline_name, flight_num))
            flight = cursor.fetchone()

            if not flight:
                flash("Flight does not exist.", "danger")
                return redirect(url_for('agent.search_flights'))

            # 检查代理是否可以为该航空公司订票
            cursor.execute("""
                SELECT * FROM booking_agent_work_for 
                WHERE email = %s AND airline_name = %s
            """, (session['user'], airline_name))
            if not cursor.fetchone():
                flash("You are not authorized to book tickets for this airline.", "danger")
                return redirect(url_for('agent.dashboard'))

            # 获取当前最大的 ticket_id
            cursor.execute("SELECT MAX(ticket_id) as max_id FROM ticket")
            result = cursor.fetchone()
            next_ticket_id = 1 if result['max_id'] is None else result['max_id'] + 1

            # 创建票务记录
            cursor.execute("""
                INSERT INTO ticket (ticket_id, airline_name, flight_num)
                VALUES (%s, %s, %s)
            """, (next_ticket_id, airline_name, flight_num))
            connection.commit()

            # 创建购买记录
            cursor.execute("""
                INSERT INTO purchases (ticket_id, customer_email, booking_agent_id, purchase_date)
                VALUES (%s, %s, %s, CURDATE())
            """, (next_ticket_id, customer_email, session['agent_id']))
            connection.commit()

            flash("Ticket successfully booked for the customer!", "success")
            return redirect(url_for('agent.dashboard'))

        # GET 请求处理
        cursor.execute("""
            SELECT airline_name, flight_num, departure_airport, arrival_airport, 
                   departure_time, arrival_time, price, status
            FROM flight 
            WHERE airline_name = %s AND flight_num = %s
        """, (airline_name, flight_num))
        flight = cursor.fetchone()

        if not flight:
            flash("Flight does not exist.", "danger")
            return redirect(url_for('agent.search_flights'))

        return render_template('agent/book_ticket_for_customer.html', flight=flight)

    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        connection.rollback()
        return redirect(url_for('agent.dashboard'))
    finally:
        cursor.close()
        connection.close()

