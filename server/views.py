from flask_apispec import MethodResource
from flask import make_response, render_template
from pymongo import MongoClient

client = MongoClient('mongodb://127.0.0.1/')
db = client.test


class HelloWorld(MethodResource):
    def get(self):
        data = db.data.find_one({'name': 'object1'})
        return make_response(render_template("index.html", data=data))