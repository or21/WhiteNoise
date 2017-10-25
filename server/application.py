import logging
import sys
from flask import Flask
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Keywords(db.Model):
    kw_id = db.Column(db.String, primary_key=True)
    kw_name = db.Column(db.String)
    last_change = db.Column(db.Date)
    campaign_name = db.Column(db.String)


def create_app():
    application = Flask(__name__)
    return application


def init_app(application):
    logging.basicConfig(filename=application.config['LOG_NAME'], level=application.config['LOG_LEVEL'], format=application.config['LOG_FORMAT'])
    if application.config['DEBUG']:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(application.config['LOG_LEVEL'])
        formatter = logging.Formatter(application.config['LOG_FORMAT'])
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)

    api = Api(application)
    api = set_resources(api)
    return api


def set_resources(api):
    from server.views import KeywordsBidSuggestions, WhiteNoise

    api.add_resource(WhiteNoise, '/', '/whitenoise')
    api.add_resource(KeywordsBidSuggestions, '/suggestions')
    return api
