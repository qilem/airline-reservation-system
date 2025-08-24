from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, current_app
from app.models.flight import Flight, Airport, Airline
from sqlalchemy import or_
from datetime import datetime
from app.models import db

public = Blueprint('public', __name__)


@public.route('/')
def index():
    """Homepage route"""
    # Get list of airports for search form autocomplete
    airports = Airport.query.all()
    airport_list = [{'name': airport.airport_name,
                     'city': airport.airport_city}
                    for airport in airports]

    return render_template('public/index.html', airports=airport_list)


@public.route('/search_result', methods=['GET'])
def search_flights():
    """Search flights based on source, destination, and date range."""
    # Get search parameters
    source = request.args.get('source', '').strip()
    destination = request.args.get('destination', '').strip()
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    try:
        # Start with a base query
        query = db.session.query(Flight)

        if source:
            # Find matching source airports by name or city
            source_airports = db.session.query(Airport.airport_name).filter(
                or_(
                    Airport.airport_name.ilike(f'%{source}%'),
                    Airport.airport_city.ilike(f'%{source}%')
                )
            ).all()
            if source_airports:
                source_names = [airport[0] for airport in source_airports]
                query = query.filter(Flight.departure_airport.in_(source_names))
            else:
                # If no matching source airport, return empty results
                return render_template(
                    'public/search_result.html',
                    flights=[],
                    source=source,
                    destination=destination,
                    start_date=start_date_str,
                    end_date=end_date_str,
                    error="No flights found for the specified source."
                )

        if destination:
            # Find matching destination airports by name or city
            dest_airports = db.session.query(Airport.airport_name).filter(
                or_(
                    Airport.airport_name.ilike(f'%{destination}%'),
                    Airport.airport_city.ilike(f'%{destination}%')
                )
            ).all()
            if dest_airports:
                dest_names = [airport[0] for airport in dest_airports]
                query = query.filter(Flight.arrival_airport.in_(dest_names))
            else:
                # If no matching destination airport, return empty results
                return render_template(
                    'public/search_result.html',
                    flights=[],
                    source=source,
                    destination=destination,
                    start_date=start_date_str,
                    end_date=end_date_str,
                    error="No flights found for the specified destination."
                )

        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            query = query.filter(Flight.departure_time >= start_date)

        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            query = query.filter(Flight.departure_time <= end_date)

        # Exclude cancelled flights and only show flights in the future
        query = query.filter(
            Flight.departure_time >= datetime.now(),
            Flight.status != 'Cancelled'
        )

        # Fetch the results
        flights = query.all()

        if not flights:
            return render_template(
                'public/search_result.html',
                flights=[],
                source=source,
                destination=destination,
                start_date=start_date_str,
                end_date=end_date_str,
                error="No flights match your search criteria."
            )

        # Prepare flight data for rendering
        flight_list = []
        for flight in flights:
            dep_airport = Airport.query.get(flight.departure_airport)
            arr_airport = Airport.query.get(flight.arrival_airport)

            flight_list.append({
                'airline': flight.airline_name,
                'flight_number': flight.flight_num,
                'departure_airport': flight.departure_airport,
                'departure_city': dep_airport.airport_city if dep_airport else '',
                'departure_time': flight.departure_time.strftime('%Y-%m-%d %H:%M'),
                'arrival_airport': flight.arrival_airport,
                'arrival_city': arr_airport.airport_city if arr_airport else '',
                'arrival_time': flight.arrival_time.strftime('%Y-%m-%d %H:%M'),
                'price': float(flight.price),
                'status': flight.status
            })

        return render_template(
            'public/search_result.html',
            flights=flight_list,
            source=source,
            destination=destination,
            start_date=start_date_str,
            end_date=end_date_str
        )

    except Exception as e:
        print(f"Error during flight search: {e}")
        return render_template(
            'public/search_result.html',
            error="An error occurred during search. Please try again.",
            flights=[],
            source=source,
            destination=destination,
            start_date=start_date_str,
            end_date=end_date_str
        )


@public.route('/flight_status', methods=['GET'])
def flight_status():
    """Check flight status by flight number or route"""
    flight_num = request.args.get('flight_num')
    airline = request.args.get('airline')
    date_str = request.args.get('date')

    if not any([flight_num, airline, date_str]):
        # If no search parameters, show search form
        return render_template('public/flight_status.html')

    try:
        query = Flight.query

        if flight_num and airline:
            # Search by flight number and airline
            query = query.filter(
                Flight.flight_num == flight_num,
                Flight.airline_name == airline
            )

        if date_str:
            # Filter by date
            search_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter(db.func.date(Flight.departure_time) == search_date)

        flights = query.all()

        # Format flight status data
        status_list = []
        for flight in flights:
            dep_airport = Airport.query.get(flight.departure_airport)
            arr_airport = Airport.query.get(flight.arrival_airport)

            status_list.append({
                'airline': flight.airline_name,
                'flight_number': flight.flight_num,
                'departure_airport': flight.departure_airport,
                'departure_city': dep_airport.airport_city,
                'scheduled_departure': flight.departure_time.strftime('%Y-%m-%d %H:%M'),
                'arrival_airport': flight.arrival_airport,
                'arrival_city': arr_airport.airport_city,
                'scheduled_arrival': flight.arrival_time.strftime('%Y-%m-%d %H:%M'),
                'status': flight.status,
                'status_time': datetime.now().strftime('%Y-%m-%d %H:%M')
            })

        return render_template('public/flight_status.html',
                               flights=status_list,
                               flight_num=flight_num,
                               airline=airline,
                               date=date_str)

    except Exception as e:
        return render_template('public/flight_status.html',
                               error="An error occurred. Please try again.",
                               flights=[],
                               flight_num=flight_num,
                               airline=airline,
                               date=date_str)


@public.route('/airports/search')
def search_airports():
    """API endpoint for airport search autocomplete"""
    search_term = request.args.get('term', '')

    airports = Airport.query.filter(
        or_(
            Airport.airport_name.ilike(f'%{search_term}%'),
            Airport.airport_city.ilike(f'%{search_term}%')
        )
    ).limit(10).all()

    results = [{
        'label': f"{airport.airport_city} ({airport.airport_name})",
        'value': airport.airport_name
    } for airport in airports]

    return jsonify(results)