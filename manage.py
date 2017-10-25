from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from server.application import db, create_app, init_app
from server.config import configure_app

application = create_app()
configure_app(application)
init_app(application)

migrate = Migrate(application, db)
manager = Manager(application)
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()

