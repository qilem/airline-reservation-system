from . import db, User
from datetime import date


class Customer(User, db.Model):
    """Customer model, maps to customer table"""
    __tablename__ = 'customer'

    email = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    building_number = db.Column(db.String(30), nullable=False)
    street = db.Column(db.String(30), nullable=False)
    city = db.Column(db.String(30), nullable=False)
    state = db.Column(db.String(30), nullable=False)
    phone_number = db.Column(db.Integer, nullable=False)
    passport_number = db.Column(db.String(30), nullable=False)
    passport_expiration = db.Column(db.Date, nullable=False)
    passport_country = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)

    # Relationship with purchases
    purchases = db.relationship('Purchases', backref='customer')


class BookingAgent(User, db.Model):
    """Booking agent model, maps to booking_agent table"""
    __tablename__ = 'booking_agent'

    email = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(50), nullable=False)
    booking_agent_id = db.Column(db.Integer, nullable=False)
    approved = db.Column(db.Boolean, default=False)  # 添加approved字段
    # Relationship with airlines they work for
    airlines = db.relationship('Airline',
                               secondary='booking_agent_work_for',
                               backref='booking_agents')

    # Relationship with purchases
    bookings = db.relationship('Purchases', backref='agent',
                               foreign_keys='Purchases.booking_agent_id')


class AirlineStaff(User, db.Model):
    """Airline staff model, maps to airline_staff table"""
    __tablename__ = 'airline_staff'

    username = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(50), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    airline_name = db.Column(db.String(50),
                             db.ForeignKey('airline.airline_name'),
                             nullable=False)
    approved = db.Column(db.Boolean, default=False)  # 添加这一行
    # Relationship with permissions
    permissions = db.relationship('Permission', backref='staff')


class Permission(db.Model):
    """Permission model for airline staff"""
    __tablename__ = 'permission'

    username = db.Column(db.String(50),
                         db.ForeignKey('airline_staff.username'),
                         primary_key=True)
    permission_type = db.Column(db.String(50), primary_key=True)


class BookingAgentWorkFor(db.Model):
    """Association table between booking agents and airlines"""
    __tablename__ = 'booking_agent_work_for'

    email = db.Column(db.String(50),
                      db.ForeignKey('booking_agent.email'),
                      primary_key=True)
    airline_name = db.Column(db.String(50),
                             db.ForeignKey('airline.airline_name'),
                             primary_key=True)