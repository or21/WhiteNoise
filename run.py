from server import application

if __name__ == '__main__':
    application.run(host='0.0.0.0', threaded=True, port=80, debug=True)