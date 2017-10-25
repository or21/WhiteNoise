import os
import logging


class BaseConfig(object):
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:Aa123456@localhost:5432/WhiteNoise'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DB_TABLE = 'keywords'
    DEBUG = True

    LOG_NAME = 'server.log'
    LOG_FORMAT = '[%(asctime)s] [%(levelname)s] [%(funcName)s]: [%(message)s]'
    LOG_LEVEL = logging.DEBUG

config = {
    "default": "server.config.BaseConfig"
}


def configure_app(app):
    config_name = os.getenv('FLASK_CONFIGURATION', 'default')
    app.config.from_object(config[config_name])
