from .application import init_app, create_app

application = create_app()
api = init_app(application)
