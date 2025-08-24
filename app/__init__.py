from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import pymysql.cursors
from config import Config
from app.models import db
from flask_wtf.csrf import CSRFProtect
from app.models.user import Customer, BookingAgent, AirlineStaff

csrf = CSRFProtect()
# 初始化全局 db 实例

login_manager = LoginManager()

def get_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='air',
        cursorclass=pymysql.cursors.DictCursor
    )

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    csrf.init_app(app)
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    app.config['GET_DB'] = get_db
    # 注册蓝图
    from app.routes.public import public
    from app.routes.auth import auth
    from app.routes.customer import customer
    from app.routes.agent import agent
    from app.routes.staff import staff

    app.register_blueprint(public)
    app.register_blueprint(auth)
    app.register_blueprint(customer)
    app.register_blueprint(agent)
    app.register_blueprint(staff)

    # 用户加载
    @login_manager.user_loader
    def load_user(user_id):
        # 尝试作为Customer加载
        customer = Customer.query.get(user_id)
        if customer:
            return customer

        # 尝试作为BookingAgent加载
        agent = BookingAgent.query.get(user_id)
        if agent:
            return agent

        # 尝试作为AirlineStaff加载
        staff = AirlineStaff.query.get(user_id)
        if staff:
            return staff

        return None


    # 工具函数
    @app.context_processor
    def utility_processor():
        return {"get_db": get_db}

    return app
