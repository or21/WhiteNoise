from flask import Flask, render_template
import json
import logging
import os
import sys


#Add project root dir
sys.path.append(os.pardir)

#Configure global logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
    # filename=globals.CONFIG['LOG_FILE'],
    filemode='w'
)

app = Flask(__name__)

#Enable auto reload on file change
app.jinja_env.auto_reload = True
# app.jinja_env.filters['tojsonadvanced'] = lambda x:json.dumps(x, cls=api.ObjectIdEncoder)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['TESTING'] = False

API_KEY = "AIzaSyDDCiGvAgO3z82SK0sGztj4C-ehj7Qc8SA"

@app.route('/')
def hello_world():
    return render_template("index.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
