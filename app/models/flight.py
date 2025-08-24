from . import db
from datetime import datetime


class Airline(db.Model):
    __tablename__ = 'airline'
    airline_name = db.Column(db.String(50), primary_key=True)
    airplanes = db.relationship('Airplane', backref='airline')
    flights = db.relationship('Flight', backref='airline', foreign_keys='Flight.airline_name')


class Airplane(db.Model):
    """Airplane model"""
    __tablename__ = 'airplane'

    airline_name = db.Column(db.String(50),
                             db.ForeignKey('airline.airline_name'),
                             primary_key=True)
    airplane_id = db.Column(db.Integer, primary_key=True)
    seats = db.Column(db.Integer, nullable=False)

    # Relationship with flights
    flights = db.relationship('Flight', backref='airplane')


class Airport(db.Model):
    """Airport model"""
    __tablename__ = 'airport'

    airport_name = db.Column(db.String(50), primary_key=True)
    airport_city = db.Column(db.String(50), nullable=False)

    # Relationships for departures and arrivals
    departures = db.relationship('Flight',
                                 backref='departure_airport_info',
                                 foreign_keys='Flight.departure_airport')
    arrivals = db.relationship('Flight',
                               backref='arrival_airport_info',
                               foreign_keys='Flight.arrival_airport')


class Flight(db.Model):
    __tablename__ = 'flight'
    airline_name = db.Column(db.String(50), db.ForeignKey('airline.airline_name'), primary_key=True)
    flight_num = db.Column(db.Integer, primary_key=True)
    departure_airport = db.Column(db.String(50),
                                  db.ForeignKey('airport.airport_name'),
                                  nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_airport = db.Column(db.String(50),
                                db.ForeignKey('airport.airport_name'),
                                nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.Numeric(10, 0), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    airplane_id = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['airline_name', 'airplane_id'],
            ['airplane.airline_name', 'airplane.airplane_id']
        ),
    )

    # Relationship with tickets
    tickets = db.relationship('Ticket', backref='flight')


class Ticket(db.Model):
    """Ticket model"""
    __tablename__ = 'ticket'

    ticket_id = db.Column(db.Integer, primary_key=True)
    airline_name = db.Column(db.String(50), nullable=False)
    flight_num = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['airline_name', 'flight_num'],
            ['flight.airline_name', 'flight.flight_num']
        ),
    )

    # Relationship with purchases
    purchase = db.relationship('Purchases', backref='ticket', uselist=False)


class Purchases(db.Model):
    """Purchases model"""
    __tablename__ = 'purchases'

    ticket_id = db.Column(db.Integer,
                          db.ForeignKey('ticket.ticket_id'),
                          primary_key=True)
    customer_email = db.Column(db.String(50),
                               db.ForeignKey('customer.email'),
                               primary_key=True)
    booking_agent_id = db.Column(db.Integer,
                                 db.ForeignKey('booking_agent.booking_agent_id'),
                                 nullable=True)
    purchase_date = db.Column(db.Date, nullable=False)