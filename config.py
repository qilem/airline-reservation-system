import os

class Config:
    # Flask配置
    SECRET_KEY = 'your-secret-key-here'  # 用于session加密

    # 数据库配置
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = ''  # 如果有密码，请填写
    DB_NAME = 'air'

    # SQLAlchemy 配置
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 关闭SQLAlchemy事件系统（推荐关闭以提高性能）

    # 其他配置
    DEBUG = True
