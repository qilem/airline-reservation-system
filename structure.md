air_ticket/ (Root directory for the airline ticketing system)
├── air.sql                         # Database schema and initial data for the airline system
├── config.py                       # Configuration settings (database connections, app settings)
├── run.py                         # Main entry point to start the application
├── structure.md                   # Documentation of project structure
└── app/                          # Main application directory
├── init.py               # Initializes the Flask application
├── allfiles.py               # Utility file for file handling operations
├── models/                   # Data models directory
│   ├── flight.py             # Flight database model and operations
│   ├── user.py               # User database model and authentication
├── routes/                   # URL routing handlers
│   ├── agent.py              # Booking agent specific routes
│   ├── auth.py               # Authentication routes (login/register)
│   ├── customer.py           # Customer specific routes
│   ├── public.py             # Public access routes
│   ├── staff.py              # Airline staff routes
├── static/                   # Static assets directory
│   ├── main.js               # Main JavaScript functionality
│   ├── style.css             # Global CSS styles
│   ├── utils.js              # Utility JavaScript functions
└── templates/                # HTML templates directory
├── base.html             # Base template other templates extend from
├── agent/                # Booking agent interface templates
│   ├── book_ticket_for_customer.html    # Agent booking interface
│   ├── commission.html                   # View commission earnings
│   ├── dashboard.html                    # Agent main dashboard
│   ├── my_flights.html                   # View booked flights
│   ├── search_flights.html               # Flight search interface
│   ├── top_customers.html                # View top customer statistics
├── auth/                 # Authentication templates
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
├── customer/             # Customer interface templates
│   ├── dashboard.html    # Customer main dashboard
│   ├── purchase.html     # Ticket purchase interface
│   ├── search_flights.html    # Flight search interface
│   ├── track_spending.html    # View spending history
│   ├── view_flights.html      # View booked flights
├── public/               # Public access templates
│   ├── flight_status.html     # Check flight status
│   ├── index.html            # Homepage
│   ├── search_result.html    # Flight search results
└── staff/                # Airline staff interface templates
├── add_airplane.html      # Add new airplane
├── add_airport.html       # Add new airport
├── add_booking_agent.html # Register new booking agents
├── approve_agent.html     # Approve booking agent requests
├── approve_staff.html     # Approve staff requests
├── create_flights.html    # Create new flights
├── dashboard.html         # Staff main dashboard
├── grant_permission.html  # Manage staff permissions
├── view_staff.html        # View all staff
├── view_agents.html       # View all booking agents
├── view_airplanes.html    # View all airplanes
├── view_customer.html     # View customer information
├── view_flights.html      # View all flights
├── view_reports.html      # View various reports