"""
This module implements a DataBase abstraction layer to get access to a postgresql.
There are three functions implemented in this module:

* insert_to_db() --> allows to write data to DB
* read_from_db() --> allows to read data from DB
* init_db() --> Initializes a database with a given name and table
* create_table --> creates a given table in the given database

@author: MMB
"""

import configparser
import psycopg2
from psycopg2 import sql, DatabaseError


def insert_to_db(
    insert_query, insert_data, db_user, db_password, db_host, db_port
) -> bool:
    """
    Inserting to database
    :param str insert_query: query used to insert to DB
    :param dict insert_data: data to be inserted to DB
    :param str db_user: username to get access to DB
    :param str db_password: password to get access to DB
    :return: bool
    """
    try:
        # Create an instance of ConfigParser
        config = configparser.ConfigParser()

        # Read the configuration file & database section
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
        cursor.execute(insert_query, insert_data)
        db_connect.commit()
        db_connect.close()

        return True

    except DatabaseError as err:
        cursor.close()
        db_connect.close()
        print("[DatabaseError Exception]", err)
        return False

    except Exception as err:
        cursor.close()
        db_connect.close()
        print("[Exception]", err)
        return False


def init_db(db_name, db_user, db_password, db_host, db_port) -> bool:
    """
    Initializes a given database if doesn't exists.
    :param str table_name: name of table to create in the db_name
    :param str db_user: username to get access to DB instance
    :param str db_password: password to get access to DB instance
    :return: bool
    """

    try:
        # Parameterized query to avoid SQL injection
        check_db_query = "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s"
        create_db = "CREATE DATABASE %s"

        db_connect = psycopg2.connect(
            database="postgres",
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )

        db_connect.autocommit = True
        cursor = db_connect.cursor()

        cursor.execute(check_db_query, (db_name,))
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(create_db, (db_name,))
            print("DataBase [{db_name}] not exist, thus created.")
        else:
            print(f"DataBase [{db_name}] exist.")

        cursor.close()
        db_connect.close()

        return True

    except DatabaseError as err:
        cursor.close()
        db_connect.close()
        print("[DatabaseError Exception]", err)
        return False

    except Exception as err:
        cursor.close()
        db_connect.close()
        print("[Exception]", err)
        return False


def create_table(db_name, table_name, db_user, db_password, db_host, db_port) -> bool:
    """
    Create a given table in the given database if doesn't exists
    :param str db_name: name of DB to create table inside it
    :param str table_name: name of table to create in the db_name
    :param str db_user: username to get access to DB instance
    :param str db_password: password to get access to DB instance
    :return: bool
    """

    try:
        create_table_query = sql.SQL(
            "CREATE TABLE IF NOT EXISTS {} (id SERIAL PRIMARY KEY, device_type varchar (150) NOT NULL, date_added date DEFAULT CURRENT_TIMESTAMP);"
        ).format(sql.Identifier(table_name))

        db_connect = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )

        db_connect.autocommit = True
        cursor = db_connect.cursor()
        cursor.execute(create_table_query)

        return True

    except DatabaseError as err:
        cursor.close()
        db_connect.close()
        print("[DatabaseError Exception]", err)
        return False

    except Exception as err:
        cursor.close()
        db_connect.close()
        print("[Exception]", err)
        return False
