import logging
from flask import Flask
from flask_restful import Api
from .utils import CONFIG
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class KeywordDb(db.Model):
    __tablename__ = CONFIG['DB_TABLE']

    kw_id = db.Column(db.String, primary_key=True)
    kw_name = db.Column(db.String)
    last_change = db.Column(db.Date)
    campaign_name = db.Column(db.String)


def create_app():
    application = Flask(__name__)
    application.config['SQLALCHEMY_DATABASE_URI'] = CONFIG['DB_URI']
    application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = CONFIG['SQLALCHEMY_TRACK_MODIFICATIONS']
    return application


def init_app(application):
    logging.basicConfig(filename=CONFIG['LOG_NAME'], level=logging.DEBUG, format=CONFIG['LOG_FORMAT'])

    api = Api(application)
    api = set_resources(api)
    return api


def set_resources(api):
    from server.views import KeywordsBidSuggestions, WhiteNoise

    api.add_resource(WhiteNoise, '/', '/whitenoise')
    api.add_resource(KeywordsBidSuggestions, '/suggestions')
    return api
