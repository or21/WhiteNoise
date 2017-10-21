from flask import Flask
from flask_restful import Api
from server.views import KeywordsBidSuggestions, WhiteNoise
import logging


def create_app():
    application = Flask(__name__)
    application.jinja_env.auto_reload = True
    application.config['TEMPLATES_AUTO_RELOAD'] = True
    application.config['TESTING'] = False
    return application


def init_app(application):
    #Configure global logging
    # TODO: create log file by script
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
        filename="/tmp/log.log",
        filemode='w'
    )
    logging.getLogger().addHandler(logging.StreamHandler())

    api = Api(application)
    api = set_resources(api)

    return api


def set_resources(api):
    api.add_resource(WhiteNoise, '/', '/whitenoise')
    api.add_resource(KeywordsBidSuggestions, '/suggestions')
    return api
