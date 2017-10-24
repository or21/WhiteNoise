from server import application
from server.utils import CONFIG

if __name__ == '__main__':
    application.run(host='0.0.0.0', threaded=True, port=CONFIG['port'])
