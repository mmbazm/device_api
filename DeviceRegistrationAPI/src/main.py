"""This is the main module of the application DeviceRegistrationAPI.
Different functions are implemented to handle functionalities of the API:

info() --> return back some information to client about the API
get_status() --> to be called for any health-check of the API
store_login_event() --> main function to handle request recieved on the path /Device/register
initilize_database() --> initialize DB for the first time of running application
check_authentication_token --> handle authentication.

Authentication is done using a token received in the header of the HTTP request.
For security reasons, it is better to send tokens in the request header.

@Author: MMB
"""

import json
import os
import configparser
import requests

from flask import jsonify, request
from src import db_layer
from src import app

# global setting
requests.adapters.DEFAULT_RETRIES = 5

# ENV variables
deviceregistration_user_key = os.getenv(
    "DEVICEREGISTRATION_USER_KEY"
)  # Token to get access to this api, this is equal to userKey
database_user = os.getenv("DATABASE_USER")
database_password = os.getenv("DATABASE_PASSWORD")
database_host = os.getenv("DATABASE_HOST")
database_port = os.getenv("DATABASE_PORT")


# implements a special class for the handling of unknown exception/errors.
# That allows formating response to client to avoid leaking eventual sensitive information from error logs.
class ThreatStackError(Exception):
    """Base Threat Stack error."""

    status_code = 500

    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        ret = dict(self.payload or ())
        ret["message"] = self.message
        return ret


class ThreatStackRequestError(ThreatStackError):
    """Threat Stack request error."""


class ThreatStackAPIError(ThreatStackError):
    """Threat API Stack error."""


# MAIN part of API
@app.errorhandler(ThreatStackError)
def handle_errors(error):
    """Handle errors of API in a structured way"""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(404)
def resource_not_found(e):
    """error handler for 404"""
    return jsonify(error="Resource not found"), 404


@app.route("/")
def info():
    """return basic information about the API to client."""
    data = """{"INFO":"DeviceRegistrationAPI MicroService"}"""
    data_json_obj = json.loads(data)
    result = app.response_class(
        response=json.dumps(data_json_obj), status=200, mimetype="application/json"
    )

    return result


@app.route("/api/status")
def get_status():
    """Get status of API"""
    data_json_obj = json.loads("""{"INFO":"DeviceRegistrationAPI status OK..."}""")
    result = app.response_class(
        response=json.dumps(data_json_obj), status=200, mimetype="application/json"
    )

    return result


@app.route("/Device/register", methods=["POST"])
def store_login_event():
    """Store information about user login event"""
    s = requests.session()
    s.keep_alive = False

    try:
        recv_api_token = request.headers.get("userKey")

        # retrieve data from request
        json_data = request.json

        if check_authentication_token(recv_api_token):
            # prepare data and query to insert to database
            data_to_insert = (str(json_data["deviceType"]),)
            insert_query = "INSERT INTO devices (device_type) VALUES (%s)"

            # call related function in DB adaptor
            res = db_layer.insert_to_db(
                insert_query,
                data_to_insert,
                database_user,
                database_password,
                database_host,
                database_port,
            )
            if res is True:
                data = {"StatusCode": 200}
                result = app.response_class(
                    response=json.dumps(data), status=200, mimetype="application/json"
                )
            else:
                data = {"StatusCode": 400}
                result = app.response_class(
                    response=json.dumps(data), status=400, mimetype="application/json"
                )
        else:
            data = {"ERROR": "Authentication failed"}
            result = app.response_class(
                response=json.dumps(data), status=403, mimetype="application/json"
            )

        return result

    except requests.exceptions.RequestException as e:
        raise ThreatStackRequestError(
            "An unexpected error is occured when storing a device type", status_code=409
        )

    except Exception as e:
        raise ThreatStackError("Unknown Error in storing DeviceType", status_code=409)


# Check validity of recieved token(i.e., userKey) for authentication
def check_authentication_token(token: str) -> bool:
    """Handle authentication of API
    :param str token-> a received token to be validated
    :return bool: True if OK otherwise False
    """
    if token == deviceregistration_user_key:
        return True

    return False


def initilize_database() -> bool:
    """
    Initialize database and create table.
    This function only executed everytime the application run. If database exists, nothing happen.
    :return bool
    """

    # Create an instance of ConfigParser
    config = configparser.ConfigParser()

    # Read the configuration file
    config.read("config/params.ini")
    conf_db = config["DATABASE"]

    res = db_layer.init_db(
        conf_db.get("NAME"),
        database_user,
        database_password,
        database_host,
        database_port,
    )

    if res:
        res = db_layer.create_table(
            conf_db.get("NAME"),
            conf_db.get("TABLE"),
            database_user,
            database_password,
            database_host,
            database_port,
        )
        if res:
            return True
        return False

    else:
        raise ThreatStackError(
            "An unexpected error is occured when initializing database", status_code=409
        )


# call initilize database when app is started, for the first time.
app.before_request_funcs = [(None, initilize_database())]
