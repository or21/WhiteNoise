import logging
from flask import Flask
from flask_restful import Api
from server.views import KeywordsBidSuggestions, WhiteNoise
from .utils import configure_log


def create_app():
    application = Flask(__name__)
    application.jinja_env.auto_reload = True
    application.config['TEMPLATES_AUTO_RELOAD'] = True
    application.config['TESTING'] = False
    return application


def init_app(application):
    #Configure global logging
    configure_log(logging.INFO, "application")
    api = Api(application)
    api = set_resources(api)

    return api


def set_resources(api):
    api.add_resource(WhiteNoise, '/', '/whitenoise')
    api.add_resource(KeywordsBidSuggestions, '/suggestions')
    return api
