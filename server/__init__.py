from .application import init_app, create_app, db
from .config import configure_app

application = create_app()
configure_app(application)
db.init_app(application)
api = init_app(application)
