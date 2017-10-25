from .application import init_app, create_app, db
from .config import configure_app

application = create_app()
configure_app(application)
db.init_app(application)
with application.app_context():
    db.create_all()
api = init_app(application)
