from flask import Blueprint

# Create blueprints with url_prefix
public = Blueprint('public', __name__, url_prefix='/')
auth = Blueprint('auth', __name__, url_prefix='/auth')
customer = Blueprint('customer', __name__, url_prefix='/customer')
agent = Blueprint('agent', __name__, url_prefix='/agent')
staff = Blueprint('staff', __name__, url_prefix='/staff')

# Import views after blueprint creation
from . import public as public_views
from . import auth as auth_views
from . import customer as customer_views
from . import agent as agent_views
from . import staff as staff_views

def init_app(app):
    app.register_blueprint(public)
    app.register_blueprint(auth)
    app.register_blueprint(customer)
    app.register_blueprint(agent)
    app.register_blueprint(staff)