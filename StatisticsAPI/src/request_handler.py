"""
This moudle handles Http requests to a remote server.
Two functions implemented:
* send_post_request() --> send a POST request to the remove through requests lib
* send_get_request() --> send a GET request to the remove through requests lib

@author: MMB
"""
import requests


def send_post_request(url, json_data, headers):
    """Send post request
    :param str url: target URL of remote server
    :param str-Json: data to send
    :param json headers: headers of http request
    :return list: request status_code & json
    """

    req = requests.post(url, data=json_data, headers=headers, verify=False, timeout=10)
    return (req.status_code, req.json())


def send_get_request(url, headers):
    """Send Get request
    :param str url: target URL of remote server
    :param json headers: headers of http request
    :return list: request status_code & json
    """
    req = requests.get(url, headers=headers, verify=False, timeout=10)

    return (req.status_code, req.json())
