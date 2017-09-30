from flask import Flask
from flask_restful import Api
from server.views import HelloWorld, Crud, AdWords, WhiteNoise
import logging


def create_app():
    application = Flask(__name__)
    #Enable auto reload on file change
    application.jinja_env.auto_reload = True
    # app.jinja_env.filters['tojsonadvanced'] = lambda x:json.dumps(x, cls=api.ObjectIdEncoder)
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

    API_KEY = "AIzaSyDDCiGvAgO3z82SK0sGztj4C-ehj7Qc8SA"
    api = Api(application)
    api = set_resources(api)

    return api


def set_resources(api):
    api.add_resource(HelloWorld, '/', '/index')
    api.add_resource(Crud, '/actions')
    api.add_resource(WhiteNoise, '/whitenoise')
    api.add_resource(AdWords, '/adwords')
    return api
