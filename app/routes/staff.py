from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, current_app
from flask import session, flash
from functools import wraps
from datetime import datetime, timedelta
from decimal import Decimal
import json
from app.models import db
from flask_wtf.csrf import CSRFProtect

staff = Blueprint('staff', __name__, url_prefix='/staff')

def get_staff_permissions(username):
    """获取员工权限"""
    db = current_app.config['GET_DB']()
    cursor = db.cursor()
    try:
        cursor.execute("""
            SELECT permission_type 
            FROM permission 
            WHERE username = %s
        """, (username,))
        permissions = [row['permission_type'] for row in cursor.fetchall()]
        return permissions
    finally:
        cursor.close()
        db.close()



def staff_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("Current session:", dict(session))  # 添加这行
        if 'user_type' not in session or session['user_type'] != 'staff':
            print("Session check failed")  # 添加这行
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@staff.route('/dashboard')
@staff_required
def dashboard():
    connection = current_app.config['GET_DB']()
    cursor = connection.cursor()
    try:
        airline = session.get('airline_name')

        # 添加获取待审批代理的查询
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM booking_agent ba
            WHERE ba.approved = FALSE
        """)
        pending_agents_result = cursor.fetchone()
        pending_agents = pending_agents_result['count'] if pending_agents_result else 0

        # 获取待审批员工数量
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM airline_staff 
            WHERE airline_name = %s AND approved = FALSE
        """, (airline,))
        pending_staff_result = cursor.fetchone()
        pending_staff = pending_staff_result['count'] if pending_staff_result else 0

        # 其他现有的查询保持不变
        flight_query = """
           SELECT f.*, 
                  dep.airport_city as departure_city,
                  arr.airport_city as arrival_city,
                  COUNT(p.ticket_id) as booked_passengers,
                  a.seats as total_seats
           FROM flight f
           JOIN airport dep ON f.departure_airport = dep.airport_name  
           JOIN airport arr ON f.arrival_airport = arr.airport_name
           JOIN airplane a ON f.airline_name = a.airline_name AND f.airplane_id = a.airplane_id
           LEFT JOIN ticket t ON f.airline_name = t.airline_name AND f.flight_num = t.flight_num
           LEFT JOIN purchases p ON t.ticket_id = p.ticket_id
           WHERE f.airline_name = %s 
           AND f.departure_time BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL 30 DAY)
           GROUP BY f.flight_num
           ORDER BY f.departure_time
           LIMIT 10
        """
        cursor.execute(flight_query, (airline,))
        recent_flights = cursor.fetchall()

        # Revenue stats
        revenue_query = """
           SELECT 
               SUM(CASE WHEN p.booking_agent_id IS NULL THEN f.price ELSE 0 END) as direct_revenue,
               SUM(CASE WHEN p.booking_agent_id IS NOT NULL THEN f.price ELSE 0 END) as indirect_revenue,
               COUNT(DISTINCT p.ticket_id) as tickets_sold
           FROM flight f
           JOIN ticket t ON f.airline_name = t.airline_name AND f.flight_num = t.flight_num
           JOIN purchases p ON t.ticket_id = p.ticket_id
           WHERE f.airline_name = %s 
           AND MONTH(p.purchase_date) = MONTH(CURRENT_DATE())
        """
        cursor.execute(revenue_query, (airline,))
        revenue = cursor.fetchone()

        # Top destinations
        dest_query = """
           SELECT 
               f.arrival_airport,
               a.airport_city,
               COUNT(*) as frequency
           FROM flight f
           JOIN airport a ON f.arrival_airport = a.airport_name
           JOIN ticket t ON f.airline_name = t.airline_name AND f.flight_num = t.flight_num
           JOIN purchases p ON t.ticket_id = p.ticket_id  
           WHERE f.airline_name = %s
           AND p.purchase_date >= DATE_SUB(NOW(), INTERVAL 3 MONTH)
           GROUP BY f.arrival_airport
           ORDER BY frequency DESC
           LIMIT 3
        """
        cursor.execute(dest_query, (airline,))
        top_destinations = cursor.fetchall()

        # Staff permissions
        perm_query = "SELECT permission_type FROM permission WHERE username = %s"
        cursor.execute(perm_query, (session.get('user'),))
        permissions = [p['permission_type'] for p in cursor.fetchall()]

        return render_template('staff/dashboard.html',
                          recent_flights=recent_flights,
                          revenue=revenue,
                          top_destinations=top_destinations,
                          permissions=permissions,
                          pending_agents=pending_agents,  # 添加这个
                          pending_staff=pending_staff)    # 添加这个
    finally:
        cursor.close()
        connection.close()


@staff.route('/approve_agents', methods=['GET', 'POST'])
@staff_required
def approve_agents():
    """
    Approve booking agents to work for the airline.
    """
    connection = current_app.config['GET_DB']()
    cursor = connection.cursor()

    try:
        print("Current session:", session)
        print("User from session:", session.get('user', 'Not found'))

        # Get admin's airline
        cursor.execute("""
            SELECT airline_name 
            FROM airline_staff 
            WHERE username = %s
        """, (session.get('user'),))
        admin_airline = cursor.fetchone()
        print("Admin airline query result:", admin_airline)

        if not admin_airline:
            flash('Unable to verify your airline.', 'danger')
            return redirect(url_for('staff.dashboard'))

        # Check admin permission
        cursor.execute("""
            SELECT * FROM permission 
            WHERE username = %s AND permission_type = 'Admin'
        """, (session.get('user'),))
        admin_permission = cursor.fetchone()
        print("Admin permission query result:", admin_permission)

        if not admin_permission:
            flash('You do not have permission to approve agents.', 'danger')
            return redirect(url_for('staff.dashboard'))

        if request.method == 'POST':
            agent_emails = request.form.getlist('agent_emails')
            if agent_emails:
                # First update the approval status
                update_query = """
                    UPDATE booking_agent
                    SET approved = TRUE
                    WHERE email IN (%s)
                """ % ','.join(['%s'] * len(agent_emails))
                cursor.execute(update_query, agent_emails)

                # Then add work relationships for approved agents
                values = [(email, admin_airline['airline_name']) for email in agent_emails]
                insert_query = """
                    INSERT INTO booking_agent_work_for (email, airline_name)
                    VALUES (%s, %s)
                """
                cursor.executemany(insert_query, values)
                connection.commit()

                flash(f'Successfully approved {len(agent_emails)} agents.', 'success')
            else:
                flash('No agents selected for approval.', 'warning')

        # Query unapproved agents
        query = """
            SELECT ba.email, ba.booking_agent_id
            FROM booking_agent ba
            WHERE ba.approved = FALSE
            AND NOT EXISTS (
                SELECT 1 
                FROM booking_agent_work_for baw
                WHERE baw.email = ba.email
                AND baw.airline_name = %s
            )
        """
        cursor.execute(query, (admin_airline['airline_name'],))
        pending_agents = cursor.fetchall()

        return render_template('staff/approve_agent.html', agents=pending_agents)
    except Exception as e:
        connection.rollback()
        flash('An error occurred while approving agents. Please try again.', 'danger')
        print("Error occurred:", str(e))
        print("Current session at error:", session)
        return redirect(url_for('staff.dashboard'))
    finally:
        cursor.close()
        connection.close()


@staff.route('/approve_staff', methods=['GET', 'POST'])
@staff_required
def approve_staff():
    connection = current_app.config['GET_DB']()
    cursor = connection.cursor()

    try:
        # 获取当前管理员的航空公司
        cursor.execute("""
            SELECT airline_name 
            FROM airline_staff 
            WHERE username = %s
        """, (session.get('user'),))
        admin_airline = cursor.fetchone()

        if not admin_airline:
            flash('Unable to verify your airline.', 'danger')
            return redirect(url_for('staff.dashboard'))

        # 检查当前用户是否有admin权限
        cursor.execute("""
            SELECT * FROM permission 
            WHERE username = %s AND permission_type = 'Admin'
        """, (session.get('user'),))
        admin_permission = cursor.fetchone()

        if not admin_permission:
            flash('You do not have permission to approve staff members.', 'danger')
            return redirect(url_for('staff.dashboard'))

        if request.method == 'POST':
            usernames = request.form.getlist('usernames')
            if usernames:
                # 修改这部分代码
                placeholders = ', '.join(['%s'] * len(usernames))
                query = f"""
                    UPDATE airline_staff
                    SET approved = TRUE
                    WHERE username IN ({placeholders})
                    AND airline_name = %s
                """
                # 构建参数列表
                params = usernames + [admin_airline['airline_name']]

                try:
                    cursor.execute(query, params)
                    connection.commit()
                    flash(f'Successfully approved {cursor.rowcount} staff members.', 'success')
                except Exception as e:
                    print(f"Update query error: {str(e)}")
                    print(f"Query: {query}")
                    print(f"Params: {params}")
                    connection.rollback()
                    flash('Error occurred during approval process.', 'danger')
            else:
                flash('No staff members selected for approval.', 'warning')

        # 查询未批准的员工
        query = """
            SELECT username, first_name, last_name, airline_name
            FROM airline_staff
            WHERE approved = FALSE
            AND airline_name = %s
        """
        cursor.execute(query, (admin_airline['airline_name'],))
        pending_staff = cursor.fetchall()

        return render_template('staff/approve_staff.html', staff=pending_staff)

    except Exception as e:
        connection.rollback()
        flash('An error occurred while approving staff. Please try again.', 'danger')
        print("Error occurred:", str(e))
        print("Current session at error:", session)
        return redirect(url_for('staff.dashboard'))
    finally:
        cursor.close()
        connection.close()


@staff.route('/view_flights')
@staff_required
def view_flights():
    """View and filter flights"""
    db = current_app.config['GET_DB']()
    cursor = db.cursor()

    # Build query based on filters
    base_query = """
        SELECT f.*, a1.airport_city as departure_city, 
               a2.airport_city as arrival_city
        FROM flight f
        JOIN airport a1 ON f.departure_airport = a1.airport_name
        JOIN airport a2 ON f.arrival_airport = a2.airport_name
        WHERE f.airline_name = %s
    """
    params = [session['airline_name']]

    if request.args.get('start_date'):
        base_query += " AND f.departure_time >= %s"
        params.append(request.args.get('start_date'))
    if request.args.get('end_date'):
        base_query += " AND f.departure_time <= %s"
        params.append(request.args.get('end_date'))
    if request.args.get('source'):
        base_query += " AND (a1.airport_name LIKE %s OR a1.airport_city LIKE %s)"
        search = f"%{request.args.get('source')}%"
        params.extend([search, search])
    if request.args.get('destination'):
        base_query += " AND (a2.airport_name LIKE %s OR a2.airport_city LIKE %s)"
        search = f"%{request.args.get('destination')}%"
        params.extend([search, search])

    base_query += " ORDER BY f.departure_time"

    cursor.execute(base_query, tuple(params))
    flights = cursor.fetchall()

    # Get staff permissions for template
    staff_permissions = get_staff_permissions(session['user'])

    cursor.close()

    return render_template('staff/view_flights.html',
                           flights=flights,
                           staff={'permissions': staff_permissions})


@staff.route('/change_status/<flight_num>', methods=['POST'])
@staff_required
def change_status(flight_num):
    """AJAX endpoint for changing flight status"""
    if 'Operator' not in get_staff_permissions(session['user']):
        return jsonify({'error': 'Permission denied'}), 403

    status = request.form.get('status')
    if not status:
        return jsonify({'error': 'Status required'}), 400

    cursor = db.cursor()
    try:
        cursor.execute("""
            UPDATE flight 
            SET status = %s 
            WHERE airline_name = %s AND flight_num = %s
        """, (status, session['airline_name'], flight_num))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()


@staff.route('/view_reports')
@staff_required
def view_reports():
    db = current_app.config['GET_DB']()
    cursor = db.cursor()

    # 获取日期范围
    end_date = request.args.get('end_date',
                                datetime.now().strftime('%Y-%m-%d'))
    start_date = request.args.get('start_date',
                                  (datetime.now() - timedelta(days=30))
                                  .strftime('%Y-%m-%d'))

    # 月度销售查询
    cursor.execute("""
        SELECT DATE_FORMAT(p.purchase_date, '%%Y-%%m') as month,
               COUNT(*) as total,
               SUM(CASE WHEN booking_agent_id IS NULL THEN 1 ELSE 0 END) 
                   as direct_sales,
               SUM(CASE WHEN booking_agent_id IS NOT NULL THEN 1 ELSE 0 END) 
                   as indirect_sales,
               SUM(f.price) as revenue,
               SUM(CASE WHEN booking_agent_id IS NULL THEN f.price ELSE 0 END) 
                   as direct_revenue,
               SUM(CASE WHEN booking_agent_id IS NOT NULL THEN f.price ELSE 0 END) 
                   as indirect_revenue
        FROM purchases p
        JOIN ticket t ON p.ticket_id = t.ticket_id
        JOIN flight f ON t.flight_num = f.flight_num AND t.airline_name = f.airline_name
        WHERE t.airline_name = %s
        AND p.purchase_date BETWEEN %s AND %s
        GROUP BY DATE_FORMAT(p.purchase_date, '%%Y-%%m')
        ORDER BY month
    """, (session['airline_name'], start_date, end_date))

    report_data = cursor.fetchall()

    # 处理数据
    months = []
    sales_data = []
    revenue_data = []

    if report_data:  # 确保有数据
        for row in report_data:
            months.append(row['month'])
            sales_data.append(row['total'])
        # 取最近一个月的直接/间接收入
        latest_row = report_data[-1] if report_data else {'direct_revenue': 0, 'indirect_revenue': 0}
        revenue_data = [
            float(latest_row['direct_revenue'] or 0),
            float(latest_row['indirect_revenue'] or 0)
        ]

    # 热门目的地查询
    cursor.execute("""
        SELECT a.airport_city, COUNT(*) as count
        FROM ticket t
        JOIN flight f ON t.flight_num = f.flight_num 
            AND t.airline_name = f.airline_name
        JOIN airport a ON f.arrival_airport = a.airport_name
        WHERE t.airline_name = %s
        AND f.departure_time >= DATE_SUB(NOW(), INTERVAL 3 MONTH)
        GROUP BY a.airport_city
        ORDER BY count DESC
        LIMIT 3
    """, (session['airline_name'],))

    top_destinations = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('staff/view_reports.html',
                           months=json.dumps(months),
                           sales_data=json.dumps(sales_data),
                           revenue_data=json.dumps(revenue_data),
                           top_destinations=top_destinations,
                           start_date=start_date,
                           end_date=end_date)


@staff.route('/create_flight', methods=['GET', 'POST'])
@staff_required
def create_flight():
    """Create new flight"""
    if 'Admin' not in get_staff_permissions(session['user']):
        flash('Permission denied', 'danger')
        return redirect(url_for('staff.dashboard'))

    db = current_app.config['GET_DB']()
    cursor = db.cursor()

    # Get available airplanes and airports
    cursor.execute("""
        SELECT airplane_id, seats 
        FROM airplane 
        WHERE airline_name = %s
        ORDER BY airplane_id
    """, (session['airline_name'],))
    airplanes = cursor.fetchall()

    cursor.execute("""
        SELECT airport_name, airport_city 
        FROM airport 
        ORDER BY airport_city
    """)
    airports = cursor.fetchall()

    if request.method == 'POST':
        try:
            # Validate departure and arrival times
            departure_time = datetime.strptime(
                request.form.get('departure_time'), '%Y-%m-%dT%H:%M')
            arrival_time = datetime.strptime(
                request.form.get('arrival_time'), '%Y-%m-%dT%H:%M')

            if departure_time >= arrival_time:
                raise ValueError("Departure time must be before arrival time")

            cursor.execute("""
                INSERT INTO flight (
                    airline_name, flight_num, departure_airport,
                    departure_time, arrival_airport, arrival_time,
                    price, status, airplane_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                session['airline_name'],
                request.form.get('flight_num'),
                request.form.get('departure_airport'),
                departure_time,
                request.form.get('arrival_airport'),
                arrival_time,
                request.form.get('price'),
                'Upcoming',
                request.form.get('airplane_id')
            ))
            db.commit()
            flash('Flight created successfully', 'success')
            return redirect(url_for('staff.view_flights'))

        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash('Error creating flight', 'danger')
        finally:
            cursor.close()

    return render_template('staff/create_flights.html',
                           airplanes=airplanes,
                           airports=airports)


@staff.route('/add_airplane', methods=['GET', 'POST'])
@staff_required
def add_airplane():
    """Add new airplane"""
    if 'Admin' not in get_staff_permissions(session['user']):
        flash('Permission denied', 'danger')
        return redirect(url_for('staff.dashboard'))

    if request.method == 'POST':

        db = current_app.config['GET_DB']()
        cursor = db.cursor()
        try:
            seats = int(request.form.get('seats'))
            if seats <= 0:
                raise ValueError("Number of seats must be positive")

            cursor.execute("""
                INSERT INTO airplane (airline_name, airplane_id, seats)
                VALUES (%s, %s, %s)
            """, (
                session['airline_name'],
                request.form.get('airplane_id'),
                seats
            ))
            db.commit()
            flash('Airplane added successfully', 'success')
            return redirect(url_for('staff.view_airplanes'))

        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash('Error adding airplane', 'danger')
        finally:
            cursor.close()

    return render_template('staff/add_airplane.html')

@staff.route('/add_airport', methods=['GET', 'POST'])
@staff_required
def add_airport():
    """
    Route to add a new airport.
    """
    # Check if the user has Admin permissions
    if 'Admin' not in get_staff_permissions(session['user']):
        flash('You do not have the required permissions to add an airport.', 'danger')
        return redirect(url_for('staff.dashboard'))

    db = current_app.config['GET_DB']()
    cursor = db.cursor()

    if request.method == 'POST':
        try:
            # Get form data
            airport_name = request.form.get('airport_name', '').strip()
            airport_city = request.form.get('airport_city', '').strip()

            # Validate input
            if not airport_name or not airport_city:
                raise ValueError("Both Airport Name and City are required.")

            # Check if the airport already exists
            cursor.execute("""
                SELECT * FROM airport WHERE airport_name = %s
            """, (airport_name,))
            if cursor.fetchone():
                raise ValueError(f"An airport with the name '{airport_name}' already exists.")

            # Insert new airport into the database
            cursor.execute("""
                INSERT INTO airport (airport_name, airport_city)
                VALUES (%s, %s)
            """, (airport_name, airport_city))
            db.commit()

            flash('Airport added successfully!', 'success')
            return redirect(url_for('staff.dashboard'))

        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            db.rollback()
            flash('An unexpected error occurred. Please try again.', 'danger')
            print(f"Error: {e}")  # Debugging log
        finally:
            cursor.close()

    return render_template('staff/add_airport.html')


@staff.route('/view_agents')
@staff_required
def view_agents():
    """View booking agents performance including zero sales"""
    db = current_app.config['GET_DB']()
    cursor = db.cursor()

    # First get all booking agents that work for this airline
    cursor.execute("""
        SELECT ba.email, ba.booking_agent_id 
        FROM booking_agent ba
        JOIN booking_agent_work_for baw ON ba.email = baw.email
        WHERE airline_name = %s
    """, (session['airline_name'],))

    all_agents = cursor.fetchall()

    # Get monthly ticket sales rankings
    cursor.execute("""
        WITH agent_monthly_sales AS (
            SELECT 
                ba.email,
                ba.booking_agent_id,
                COUNT(p.ticket_id) as ticket_count
            FROM booking_agent ba
            JOIN booking_agent_work_for baw ON ba.email = baw.email
            LEFT JOIN purchases p ON ba.booking_agent_id = p.booking_agent_id
            LEFT JOIN ticket t ON p.ticket_id = t.ticket_id
            WHERE baw.airline_name = %s
            AND (p.purchase_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH) OR p.purchase_date IS NULL)
            GROUP BY ba.email, ba.booking_agent_id
            ORDER BY ticket_count DESC
            LIMIT 5
        )
        SELECT 
            email,
            booking_agent_id,
            ticket_count,
            RANK() OVER (ORDER BY ticket_count DESC) as rank_num
        FROM agent_monthly_sales
    """, (session['airline_name'],))

    top_monthly_sales = cursor.fetchall()

    # Get yearly ticket sales rankings
    cursor.execute("""
        WITH agent_yearly_sales AS (
            SELECT 
                ba.email,
                ba.booking_agent_id,
                COUNT(p.ticket_id) as ticket_count
            FROM booking_agent ba
            JOIN booking_agent_work_for baw ON ba.email = baw.email
            LEFT JOIN purchases p ON ba.booking_agent_id = p.booking_agent_id
            LEFT JOIN ticket t ON p.ticket_id = t.ticket_id
            WHERE baw.airline_name = %s
            AND (p.purchase_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) OR p.purchase_date IS NULL)
            GROUP BY ba.email, ba.booking_agent_id
            ORDER BY ticket_count DESC
            LIMIT 5
        )
        SELECT 
            email,
            booking_agent_id,
            ticket_count,
            RANK() OVER (ORDER BY ticket_count DESC) as rank_num
        FROM agent_yearly_sales
    """, (session['airline_name'],))

    top_yearly_sales = cursor.fetchall()

    # Get yearly commission rankings
    cursor.execute("""
        WITH agent_yearly_commission AS (
            SELECT 
                ba.email,
                ba.booking_agent_id,
                COALESCE(SUM(f.price * 0.1), 0) as commission
            FROM booking_agent ba
            JOIN booking_agent_work_for baw ON ba.email = baw.email
            LEFT JOIN purchases p ON ba.booking_agent_id = p.booking_agent_id
            LEFT JOIN ticket t ON p.ticket_id = t.ticket_id
            LEFT JOIN flight f ON t.flight_num = f.flight_num AND t.airline_name = f.airline_name
            WHERE baw.airline_name = %s
            AND (p.purchase_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) OR p.purchase_date IS NULL)
            GROUP BY ba.email, ba.booking_agent_id
            ORDER BY commission DESC
            LIMIT 5
        )
        SELECT 
            email,
            booking_agent_id,
            commission,
            RANK() OVER (ORDER BY commission DESC) as rank_num
        FROM agent_yearly_commission
    """, (session['airline_name'],))

    top_yearly_commission = cursor.fetchall()

    # If we have less than 5 agents in any category, fill with remaining agents (with 0 values)
    def fill_to_five(rankings, all_agents):
        if len(rankings) < 5:
            used_ids = {r['booking_agent_id'] for r in rankings}
            extras = [
                         {
                             'email': agent['email'],
                             'booking_agent_id': agent['booking_agent_id'],
                             'ticket_count': 0 if 'ticket_count' in rankings[0] else None,
                             'commission': 0 if 'commission' in rankings[0] else None,
                             'rank_num': len(rankings) + i + 1
                         }
                         for i, agent in enumerate(all_agents)
                         if agent['booking_agent_id'] not in used_ids
                     ][:5 - len(rankings)]
            rankings.extend(extras)
        return rankings

    top_monthly_sales = fill_to_five(list(top_monthly_sales), all_agents)
    top_yearly_sales = fill_to_five(list(top_yearly_sales), all_agents)
    top_yearly_commission = fill_to_five(list(top_yearly_commission), all_agents)

    cursor.close()
    db.close()

    return render_template('staff/view_agents.html',
                           top_monthly_sales=top_monthly_sales,
                           top_yearly_sales=top_yearly_sales,
                           top_yearly_commission=top_yearly_commission)

@staff.route('/view_customers')
@staff_required
def view_customers():
    """View customer information and flight history"""
    db = current_app.config['GET_DB']()
    cursor = db.cursor()

    # Get most frequent customer
    cursor.execute("""
        SELECT c.email, c.name, COUNT(*) as flights_count
        FROM purchases p
        JOIN customer c ON p.customer_email = c.email
        JOIN ticket t ON p.ticket_id = t.ticket_id
        WHERE t.airline_name = %s
        AND p.purchase_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
        GROUP BY c.email, c.name
        ORDER BY flights_count DESC
        LIMIT 1
    """, (session['airline_name'],))

    frequent_customer = cursor.fetchone()

    # Get specific customer's flights if requested
    customer_flights = None
    if request.args.get('customer_email'):
        cursor.execute("""
            SELECT f.*, p.purchase_date,
                   a1.airport_city as departure_city,
                   a2.airport_city as arrival_city
            FROM flight f
            JOIN ticket t ON f.flight_num = t.flight_num 
                AND f.airline_name = t.airline_name
            JOIN purchases p ON t.ticket_id = p.ticket_id
            JOIN airport a1 ON f.departure_airport = a1.airport_name
            JOIN airport a2 ON f.arrival_airport = a2.airport_name
            WHERE f.airline_name = %s 
            AND p.customer_email = %s
            ORDER BY f.departure_time DESC
        """, (session['airline_name'], request.args.get('customer_email')))
        customer_flights = cursor.fetchall()

    cursor.close()

    return render_template('staff/view_customer.html',
                           frequent_customer=frequent_customer,
                           customer_flights=customer_flights)


@staff.route('/view_staff')
@staff_required
def view_staff():
    """View all staff from the same airline (admin only)"""
    db = current_app.config['GET_DB']()
    cursor = db.cursor()

    # Check admin permission
    cursor.execute("""
        SELECT * FROM permission 
        WHERE username = %s AND permission_type = 'Admin'
    """, (session['user'],))

    is_admin = cursor.fetchone() is not None

    if not is_admin:
        return jsonify({'error': 'You do not have permission to view this page.'})

    # Get all staff from the same airline with their permissions
    cursor.execute("""
        SELECT 
            s.username,
            s.first_name,
            s.last_name,
            s.date_of_birth,
            GROUP_CONCAT(DISTINCT p.permission_type) as permissions
        FROM airline_staff s
        LEFT JOIN permission p ON s.username = p.username
        WHERE s.airline_name = %s
        GROUP BY s.username, s.first_name, s.last_name, s.date_of_birth
        ORDER BY s.first_name, s.last_name
    """, (session['airline_name'],))

    staff_list = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('staff/view_staff.html', staff_list=staff_list)


@staff.route('/grant_permission', methods=['GET', 'POST'])
@staff_required
def grant_permission():
    """Grant permissions to other staff members"""
    if 'Admin' not in get_staff_permissions(session['user']):
        flash('Permission denied', 'danger')
        return redirect(url_for('staff.dashboard'))

    db = current_app.config['GET_DB']()
    cursor = db.cursor()

    if request.method == 'POST':
        try:
            # Check if staff member exists and works for same airline
            cursor.execute("""
                SELECT * FROM airline_staff
                WHERE username = %s AND airline_name = %s
            """, (request.form.get('username'), session['airline_name']))

            if not cursor.fetchone():
                raise ValueError("Staff member not found or not authorized")

            cursor.execute("""
                INSERT INTO permission (username, permission_type)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE permission_type = VALUES(permission_type)
            """, (
                request.form.get('username'),
                request.form.get('permission_type')
            ))
            db.commit()
            flash('Permission granted successfully', 'success')
            return redirect(url_for('staff.dashboard'))

        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash('Error granting permission', 'danger')

    # Get staff members without all permissions
    cursor.execute("""
        SELECT s.username, s.first_name, s.last_name,
               GROUP_CONCAT(p.permission_type) as current_permissions
        FROM airline_staff s
        LEFT JOIN permission p ON s.username = p.username
        WHERE s.airline_name = %s
        GROUP BY s.username
        HAVING current_permissions IS NULL 
            OR current_permissions NOT LIKE '%Admin%'
    """, (session['airline_name'],))

    staff_members = cursor.fetchall()
    cursor.close()

    return render_template('staff/grant_permission.html',
                           staff_members=staff_members)


@staff.route('/add_booking_agent', methods=['GET', 'POST'])
@staff_required
def add_booking_agent():
    """Add booking agent to airline"""
    if 'Admin' not in get_staff_permissions(session['user']):
        flash('Permission denied', 'danger')
        return redirect(url_for('staff.dashboard'))

    db = current_app.config['GET_DB']()
    cursor = db.cursor()

    if request.method == 'POST':
        try:
            # Check if agent exists
            cursor.execute("""
                SELECT * FROM booking_agent 
                WHERE email = %s
            """, (request.form.get('email'),))

            if not cursor.fetchone():
                raise ValueError("Booking agent not found")

            # Check if already working for this airline
            cursor.execute("""
                SELECT * FROM booking_agent_work_for
                WHERE email = %s AND airline_name = %s
            """, (request.form.get('email'), session['airline_name']))

            if cursor.fetchone():
                raise ValueError("Agent already works for this airline")

            # Add work relationship
            cursor.execute("""
                INSERT INTO booking_agent_work_for (email, airline_name)
                VALUES (%s, %s)
            """, (request.form.get('email'), session['airline_name']))

            db.commit()
            flash('Booking agent added successfully', 'success')
            return redirect(url_for('staff.view_agents'))

        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash('Error adding booking agent', 'danger')

    # Get available agents
    cursor.execute("""
        SELECT ba.*
        FROM booking_agent ba
        WHERE ba.email NOT IN (
            SELECT email 
            FROM booking_agent_work_for 
            WHERE airline_name = %s
        )
    """, (session['airline_name'],))

    available_agents = cursor.fetchall()
    cursor.close()

    return render_template('staff/add_booking_agent.html',
                           available_agents=available_agents)

@staff.route('/view_airplanes')
@staff_required
def view_airplanes():
    """View and manage airplanes"""
    db = current_app.config['GET_DB']()
    cursor = db.cursor()

    try:
        # Query to fetch airplanes for the airline
        query = """
            SELECT airplane_id, seats
            FROM airplane
            WHERE airline_name = %s
            ORDER BY airplane_id
        """
        cursor.execute(query, (session['airline_name'],))
        airplanes = cursor.fetchall()

        return render_template('staff/view_airplanes.html', airplanes=airplanes)
    except Exception as e:
        flash("An error occurred while fetching airplanes. Please try again.", "danger")
        print("Error:", e)
        return redirect(url_for('staff.dashboard'))
    finally:
        cursor.close()
