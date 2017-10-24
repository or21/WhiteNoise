from .application import init_app, create_app, db

application = create_app()
db.init_app(application)
with application.app_context():
    db.create_all()
api = init_app(application)
