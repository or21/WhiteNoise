from flask_apispec import MethodResource
from flask import make_response, render_template, request
from pymongo import MongoClient

client = MongoClient('mongodb://127.0.0.1/')
db = client.test


class HelloWorld(MethodResource):
    def get(self):
        data = db.data.find_one({'first name': 'Or'})
        return make_response(render_template("index.html", data=data))


class Crud(MethodResource):
    def get(self):
        return crud_router()

    def post(self):
        return crud_router(request)


def crud_router(request_form=None):
    message = "Please fill the form"
    if request_form:
        action = request_form.form['action']
        firstname = request_form.form['firstname']
        lastname = request_form.form['lastname']
    else:
        action = ""

    if action == 'Filter':
        filtered = list(db.data.find({'last name': lastname}))
        print filtered
        if filtered:
            message = "Filtered by last name - " + lastname
            return make_response(render_template("actions.html", data=filtered, message=message))
        else:
            message = "Could not find instance. Reminder - you can only filter by last name"

    if action == 'Add':
        if db.data.find_one({'first name': firstname}):
            message = "There is already instance with first name  " + firstname
        else:
            message += "Inserted " + firstname + " " + lastname
            db.data.insert_one({'first name': firstname, 'last name': lastname})

    if action == 'Update':
        element = db.data.find_one({'first name': firstname})
        if list(element):
            if element['last name'] == lastname:
                message = "Nothing to update"
            else:
                message = "Updated " + firstname + " last name to: " + lastname
                db.data.update_one({'first name': firstname},
                                   {'$set': {'first name': firstname, 'last name': lastname}})
        else:
            message = "Could not update. No instance for first name " + firstname

    if action == 'Delete':
        if db.data.find_one({'first name': firstname}):
            message = "Delete where first name is " + firstname
            db.data.delete_one({'first name': firstname})
        else:
            message = "Could not delete. No instance with first name " + firstname

    data = list(db.data.find({}))
    return make_response(render_template("actions.html", data=data, message=message))
