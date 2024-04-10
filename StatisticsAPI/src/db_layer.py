"""
This module implements a DataBase abstraction layer to get access to a postgresql DB.
There is one function implemented in this module:

* read_from_db() --> allows to read data from DB

@author: MMB
"""
import configparser
import psycopg2
from psycopg2 import DatabaseError


def read_from_db(
    select_query, select_key, db_user, db_password, db_host, db_port
) -> (bool, list):
    """
    Reading from database
    :param str select_query: query used to select data from DB
    :param str selecy_key: used in the select query in the condition
    :param str db_user: username to get access to DB
    :param str db_password: password to get access to DB
    :param str db_host: host of DB instance
    :param str db_port: port of DB instance
    :return: list otherwise an empty list
    """

    try:
        # Read the configuration file and DATABASE section
        config = configparser.ConfigParser()
        config.read("config/params.ini")
        conf_db = config["DATABASE"]

        db_connect = psycopg2.connect(
            database=conf_db.get("NAME"),
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )

        cursor = db_connect.cursor()
        cursor.execute(select_query, select_key)
        result = cursor.fetchall()

        cursor.close()
        db_connect.close()

        return (True, result)

    except DatabaseError as err:
        cursor.close()
        db_connect.close()
        print("[DatabaseError Exception]", err)

        return (False, [])

    except Exception as err:
        cursor.close()
        db_connect.close()
        print("[Exception]", err)

        return (False, [])
