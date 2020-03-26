# -*- coding: utf-8 -*-
import os
import sys
import datetime
import mysql.connector
import urllib.parse
import psycopg2
import configparser

from psycopg2.extras import RealDictCursor
from passlib.hash import sha256_crypt

from flask import request

from flask_restful import Resource, Api, reqparse
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, decode_token
)

from models.token_model import TokenModel

parser = reqparse.RequestParser()


def token_decode(token):
    de = decode_token(token)
    if 'identity' in de:
        iden = de['identity']
        return iden
    else:
        return False


class Activity:

    class Model:

        def __init__(self):
            try:
                config = configparser.ConfigParser()

                dirname = os.path.abspath(os.path.dirname(__file__))
                config_path = os.path.join(dirname, '../.config.ini')
                config.read(config_path)

                host = config.get('dbsettings', 'db_host')
                user = config.get('dbsettings', 'db_user')
                passwd = config.get('dbsettings', 'db_passwd')
                dbname = config.get('dbsettings', 'db_dbname')
                self.db = psycopg2.connect(
                    database=dbname, user=user, password=passwd, host=host)
            except Exception as err:
                print(str(err), ' could not connect to db')
                sys.exit()

        def convert_timestamp(self, value):
            return value.strftime("%Y-%m-%d %H:%M:%S")

        def get_total(self):
            try:
                cur = self.db.cursor(cursor_factory=RealDictCursor)
                query = """SELECT count(*) AS total FROM ocean_color_satmo_nc AS s;"""
                cur.execute(query)
                row = cur.fetchone()
                cur.close()
                if row:
                    return row['total']
                else:
                    return None
            except psycopg2.Error as err:
                self.db.rollback()
                raise Exception(err)

        def get_rows(self, c_page=1, p_size=10):
            try:
                cur = self.db.cursor(cursor_factory=RealDictCursor)
                query = """SELECT l.id, u.username, l.ip, l.activity, l.created_at FROM systems_users_log AS l LEFT JOIN systems_users AS u ON u.id = l.user_id ORDER BY "created_at" DESC LIMIT %s OFFSET %s;""" % (
                    p_size, (c_page - 1) * p_size)
                cur.execute(query)
                rows = cur.fetchall()
                cur.close()
                if rows:
                    arr = []
                    for row in rows:
                        arr.append({
                            'id': row['id'],
                            'username': row['username'],
                            'ip': row['ip'],
                            'activity': row['activity'],
                            'created_at': self.convert_timestamp(row['created_at'])
                        })
                    return arr
                else:
                    return []
            except psycopg2.Error as err:
                self.db.rollback()
                raise Exception(err)

    class ARows(Resource):

        def __init__(self):
            c = Activity()
            self.model = c.Model()

        def post(self):
            try:
                parser.add_argument('token', type=str)
                parser.add_argument('currentPage', type=int)
                parser.add_argument('pageSize', type=int)
                args = parser.parse_args()
                iden = token_decode(args['token'])
                if iden:
                    rows = self.model.get_rows(
                        c_page=args['currentPage'], p_size=args['pageSize'])
                    return {
                        "success": True,
                        "email": iden['email'],
                        "profile_img": iden['profile_img'],
                        "rows": rows,
                        "total": self.model.get_total()
                    }
                else:
                    raise Exception("Invalid token")
            except Exception as error:
                return {"success": False, "message": str(error)}
