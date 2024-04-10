"""This is the main module of the application StatisticsAPI.
Different functions are implemented to handle functionalities of the API:

info() --> return back some information to client about the API
get_status() --> to be called for any health-check of the API
send_login_event() --> main function to handle request recieved on the path /Device/register
get_device_count() --> to rerieve count of deviceType sent by client
check_authentication_token --> handle authentication part.

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
from src import request_handler
from src import app

# global setting
requests.adapters.DEFAULT_RETRIES = 5

# ENV variables
statistics_user_key = os.getenv("STATISTICS_USER_KEY")
deviceregistrationapi_host = os.getenv("DEVICEREGISTRATIONAPI_HOST")
deviceregistrationapi_port = os.getenv("DEVICEREGISTRATIONAPI_PORT")
database_host = os.getenv("DATABASE_HOST")
database_port = os.getenv("DATABASE_PORT")
database_user = os.getenv("DATABASE_USER")
database_password = os.getenv("DATABASE_PASSWORD")


# implements a special class for handling of unknown exception/errors.
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
    """Handle errors of API in a structured way through ThreatStackError class"""
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
    data = """{"INFO":"StatisticsAPI component"}"""
    data_json_obj = json.loads(data)
    result = app.response_class(
        response=json.dumps(data_json_obj), status=200, mimetype="application/json"
    )

    return result


@app.route("/api/status")
def get_status():
    """Get status of API"""
    data = """{"INFO":"StatisticsAPI status OK..."}"""
    data_json_obj = json.loads(data)
    result = app.response_class(
        response=json.dumps(data_json_obj), status=200, mimetype="application/json"
    )

    return result


@app.route("/Log/auth", methods=["POST"])
def send_login_event():
    """Store information about user login event"""
    s = requests.session()
    s.keep_alive = False

    # Read the configuration file and DEVICEREGISTRATIONAPI section
    config = configparser.ConfigParser()
    config.read("config/params.ini")
    conf_deviceregfistration = config["DEVICEREGISTRATIONAPI"]

    # Deviceregistration Api target URL
    deviceregistration_api_url = "http://{}:{}{}".format(
        deviceregistrationapi_host,
        deviceregistrationapi_port,
        conf_deviceregfistration.get("ENDPOINT_STORE_EVENT"),
    )

    try:
        recv_api_token = request.headers.get("userKey")
        # retrieve data from request
        json_data = request.json

        if check_authentication_token(recv_api_token):
            # check if body contain device_type & user_key header

            if len(json_data["deviceType"]) == 0:
                raise ValueError("Null value in Json.")

            data = {"deviceType": str(json_data["deviceType"])}
            headers = {"Content-Type": "application/json", "userKey": recv_api_token}

            # send request to DeviceRegistrationAPI
            res = request_handler.send_post_request(
                deviceregistration_api_url, json.dumps(data), headers
            )

            if res[0] == 200:
                data = {
                    "StatusCode": res[0],
                    "message": "success",
                }
                result = app.response_class(
                    response=json.dumps(data),
                    status=res[0],
                    mimetype="application/json",
                )
            elif res[0] == 400:
                data = {
                    "StatusCode": res[0],
                    "message": "bad_request",
                }
                result = app.response_class(
                    response=json.dumps(data),
                    status=res[0],
                    mimetype="application/json",
                )
            else:
                data = {
                    "StatusCode": 409,
                    "message": "An error occured during device registration",
                }
                result = app.response_class(
                    response=json.dumps(data),
                    status=409,
                    mimetype="application/json",
                )

        else:
            data = {"ERROR": "Authentication failed", "StatusCode": "403"}
            result = app.response_class(
                response=json.dumps(data), status=403, mimetype="application/json"
            )

        return result

    except (TypeError, ValueError, KeyError, json.JSONDecodeError):
        raise ThreatStackRequestError(
            "Invalide JSON data, Key, syntax or value.", status_code=400
        )
    except requests.exceptions.RequestException as e:
        raise ThreatStackRequestError(
            "Error in request for storing DeviceType [{}]".format(json_data["deviceType"]),
            status_code=500,
        )

    except Exception as e:
        raise ThreatStackError(
            "Unknown Error in storing DeviceType [{}]".format(json_data["deviceType"]),
            status_code=500,
        )


@app.route("/Log/auth/statistics/<string:deviceType>", methods=["GET"])
def get_device_count(deviceType: str):
    """Retrieve the amount of devices registered by type"""

    DEVICE_TYPE_RECEIVED = deviceType

    # parameterized SQL query to qvoid SQL Injection attacks.
    select_query = "SELECT * FROM devices WHERE device_type=%s"

    try:
        res = db_layer.read_from_db(
            select_query,
            (DEVICE_TYPE_RECEIVED,),
            database_user,
            database_password,
            database_host,
            database_port,
        )
        if res[0]:
            if len(res[1]) == 0:
                data = {"deviceType": DEVICE_TYPE_RECEIVED, "count": "-1"}
                result = app.response_class(
                    response=json.dumps(data), status=200, mimetype="application/json"
                )

            else:
                data = {"deviceType": DEVICE_TYPE_RECEIVED, "count": len(res[1])}
                result = app.response_class(
                    response=json.dumps(data), status=200, mimetype="application/json"
                )
        else:
            data = {"Error Message": "Fetching resulted in Error"}
            result = app.response_class(
                response=json.dumps(data), status=520, mimetype="application/json"
            )

        return result

    except requests.exceptions.RequestException as e:
        raise ThreatStackRequestError(
            "Error in retreiving count of DeviceType", status_code=409
        )

    except Exception as e:
        raise ThreatStackError(
            "Unknown Error in retreiving count of DeviceType [{}]".format(deviceType),
            status_code=409,
        )


# Check validity of recieved token(i.e., userKey) for authentication
def check_authentication_token(token: str) -> bool:
    """Handle authentication of API
    :param str token-> a received token to be validated
    :return bool: True if OK otherwise False
    """
    if token == statistics_user_key:
        return True

    return False
