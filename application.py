import os
import sys
import json

import flask
from flask import request, Response

from boto import dynamodb2
from boto.dynamodb2.table import Table
from boto.dynamodb2.items import Item
from boto.dynamodb2.fields import HashKey
from boto.dynamodb2.exceptions import ConditionalCheckFailedException
from boto.exception import JSONResponseError

# Default config vals
THEME = 'default' if os.environ.get('THEME') is None else os.environ.get('THEME')
FLASK_DEBUG = 'false' if os.environ.get('FLASK_DEBUG') is None else os.environ.get('FLASK_DEBUG')

# Create the Flask app
application = flask.Flask(__name__)

# Load config values specified above
application.config.from_object(__name__)

# Load configuration vals from a file
application.config.from_pyfile('application.config', silent=True)

# Only enable Flask debugging if an env var is set to true
application.debug = application.config['FLASK_DEBUG'] in ['true', 'True']

# Connect to DynamoDB and get ref to Table
ddb_conn = dynamodb2.connect_to_region(application.config['AWS_REGION'])
ddb_table = Table(table_name=application.config['STARTUP_SIGNUP_TABLE'],
                  connection=ddb_conn)

@application.route('/')
def welcome():
    theme = application.config['THEME']
    return flask.render_template('index.html', theme=theme, flask_debug=application.debug)


@application.route('/signup', methods=['POST'])
def signup():
    signup_data = dict()
    for item in request.form:
        signup_data[item] = request.form[item]

    try:
        store_in_dynamo(signup_data)
    except ConditionalCheckFailedException:
        return Response("", status=409, mimetype='application/json')

    return Response(json.dumps(signup_data), status=201, mimetype='application/json')


def store_in_dynamo(signup_data):
    signup_item = Item(ddb_table, data=signup_data)
    signup_item.save()


def init_db():
    try:
        ddb_table.describe()
    except JSONResponseError:
        print "Could not connect to DynamoDB table"

if __name__ == '__main__':
    init_db()
    application.run(host='0.0.0.0')