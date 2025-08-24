Air Ticket System Use Cases and Database Queries
Customer Use Cases
1. View/Search Flights
Use Case: Customers can search for available flights by source, destination, and date
sqlCopySELECT f.*, a1.city as departure_city, a2.city as arrival_city 
FROM flight f 
JOIN airport a1 ON f.departure_airport = a1.code 
JOIN airport a2 ON f.arrival_airport = a2.code 
WHERE f.departure_airport = %s 
  AND f.arrival_airport = %s 
  AND DATE(f.departure_time) = %s
2. Purchase Tickets
Use Case: Customer purchases a ticket for a specific flight
sqlCopy-- Check available seats
SELECT seats - COUNT(*) as available_seats 
FROM flight f 
LEFT JOIN ticket t ON f.flight_number = t.flight_number 
WHERE f.flight_number = %s

-- Insert ticket purchase
INSERT INTO ticket (customer_email, flight_number, price) 
VALUES (%s, %s, %s)
3. Track Spending
Use Case: View purchase history and spending statistics
sqlCopy-- Total spending in date range
SELECT SUM(price) as total_spent 
FROM ticket 
WHERE customer_email = %s 
  AND purchase_date BETWEEN %s AND %s

-- Monthly spending breakdown
SELECT DATE_FORMAT(purchase_date, '%Y-%m') as month, SUM(price) as spent 
FROM ticket 
WHERE customer_email = %s 
GROUP BY month
Booking Agent Use Cases
1. Book for Customers
Use Case: Agents can purchase tickets on behalf of customers
sqlCopyINSERT INTO ticket (customer_email, flight_number, booking_agent_id, price) 
VALUES (%s, %s, %s, %s)
2. View Commission
Use Case: Track commission earnings from ticket sales
sqlCopySELECT SUM(price * commission_rate) as total_commission 
FROM ticket 
WHERE booking_agent_id = %s 
  AND purchase_date BETWEEN %s AND %s
3. Top Customers
Use Case: View statistics about top customers by tickets/commission
sqlCopySELECT customer_email, COUNT(*) as tickets_bought 
FROM ticket 
WHERE booking_agent_id = %s 
GROUP BY customer_email 
ORDER BY tickets_bought DESC 
LIMIT 5
Airline Staff Use Cases
1. Create New Flights
Use Case: Staff can create and schedule new flights
sqlCopyINSERT INTO flight (flight_number, departure_airport, arrival_airport, 
                   departure_time, arrival_time, price, airplane_id) 
VALUES (%s, %s, %s, %s, %s, %s, %s)
2. Change Flight Status
Use Case: Update flight status (delayed, on-time, etc.)
sqlCopyUPDATE flight 
SET status = %s 
WHERE flight_number = %s
3. View Reports
Use Case: Generate various business reports
sqlCopy-- Ticket sales in date range
SELECT COUNT(*) as tickets_sold, SUM(price) as total_revenue 
FROM ticket t 
JOIN flight f ON t.flight_number = f.flight_number 
WHERE purchase_date BETWEEN %s AND %s

-- Popular destinations
SELECT arrival_airport, COUNT(*) as visits 
FROM flight f 
JOIN ticket t ON f.flight_number = t.flight_number 
GROUP BY arrival_airport 
ORDER BY visits DESC
4. Manage Staff/Agents
Use Case: Approve new accounts and manage permissions
sqlCopy-- Approve new staff
UPDATE airline_staff 
SET status = 'approved' 
WHERE username = %s

-- Grant permissions
INSERT INTO permission (username, permission_type) 
VALUES (%s, %s)
Public Use Cases
1. Check Flight Status
Use Case: Anyone can check flight status without login
sqlCopySELECT flight_number, status, departure_time, arrival_time 
FROM flight 
WHERE flight_number = %s
2. View Flight Schedule
Use Case: Browse available flights
sqlCopySELECT f.*, a1.city as from_city, a2.city as to_city 
FROM flight f 
JOIN airport a1 ON f.departure_airport = a1.code 
JOIN airport a2 ON f.arrival_airport = a2.code 
WHERE departure_time > NOW() 
ORDER BY departure_time
Authentication Use Cases
1. User Registration
Use Case: Register new user accounts
sqlCopy-- Customer registration
INSERT INTO customer (email, name, password, phone) 
VALUES (%s, %s, %s, %s)

-- Agent registration
INSERT INTO booking_agent (email, password) 
VALUES (%s, %s)

-- Staff registration
INSERT INTO airline_staff (username, airline_name, password) 
VALUES (%s, %s, %s)
2. User Login
Use Case: Authenticate users
sqlCopy-- Check credentials (example for customer)
SELECT * FROM customer 
WHERE email = %s AND password = %s
Data Management
1. Add New Airplane
Use Case: Staff can add new airplanes to the system
sqlCopyINSERT INTO airplane (airline_name, seats) 
VALUES (%s, %s)
2. Add New Airport
Use Case: Staff can add new airports
sqlCopyINSERT INTO airport (code, name, city, country) 
VALUES (%s, %s, %s, %s)
Note: All queries shown use parameterized statements (%s) to prevent SQL injection. Actual implementation includes additional security measures and error handling.