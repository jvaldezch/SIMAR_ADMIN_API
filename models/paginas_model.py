# -*- coding: utf-8 -*-
import os
import sys
import datetime
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


class Pages:

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
            if value:
                return value.strftime("%Y-%m-%d %H:%M:%S")
            else:
                return None

        def get_total(self):
            try:
                cur = self.db.cursor(cursor_factory=RealDictCursor)
                query = """SELECT count(*) AS total FROM systems_pages AS s;"""
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
                query = """SELECT * FROM systems_pages ORDER BY "created_at" DESC LIMIT %s OFFSET %s;""" % (
                    p_size, (c_page - 1) * p_size)
                cur.execute(query)
                rows = cur.fetchall()
                cur.close()
                if rows:
                    arr = []
                    for row in rows:
                        arr.append({
                            'id': row['id'],
                            'name': row['name'],
                            'description': row['description'],
                            'created_at': self.convert_timestamp(row['created_at']),
                            'updated_at': self.convert_timestamp(row['updated_at'])
                        })
                    return arr
                else:
                    return []
            except psycopg2.Error as err:
                self.db.rollback()
                raise Exception(err)

        def get_row(self, id):
            try:
                cur = self.db.cursor(cursor_factory=RealDictCursor)
                query = """SELECT * FROM systems_pages AS c WHERE c.id = %s;""" % id
                cur.execute(query)
                row = cur.fetchone()
                cur.close()
                if row:
                    return {
                        'id': row['id'],
                        'name': row['name'],
                        'description': row['description'],
                        'created_at': self.convert_timestamp(row['created_at']),
                        'updated_at': self.convert_timestamp(row['updated_at'])
                    }
                else:
                    return None
            except psycopg2.Error as err:
                self.db.rollback()
                raise Exception(err)

        def update_row_metadata(self, id, desc):
            try:
                cur = self.db.cursor(cursor_factory=RealDictCursor)
                query = """UPDATE systems_pages SET "description" = '%s' WHERE id = %s;""" % (
                    desc, id)
                cur.execute(query)
                self.db.commit()
                return True
            except psycopg2.Error as err:
                self.db.rollback()
                raise Exception(err)

    class PGRows(Resource):

        def __init__(self):
            c = Pages()
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

    class PGRow(Resource):

        def __init__(self):
            c = Pages()
            self.model = c.Model()

        def post(self):
            try:
                parser.add_argument('token', type=str)
                parser.add_argument('id', type=int)
                args = parser.parse_args()
                iden = token_decode(args['token'])
                if iden:
                    row = self.model.get_row(args['id'])
                    return {
                        "success": True,
                        "email": iden['email'],
                        "profile_img": iden['profile_img'],
                        "row": row
                    }
                else:
                    raise Exception("Invalid token")
            except Exception as error:
                return {"success": False, "message": str(error)}

    class PGRowMetadata(Resource):

        def __init__(self):
            c = Pages()
            self.model = c.Model()

        def post(self):
            try:
                parser.add_argument('token', type=str)
                parser.add_argument('id', type=int)
                args = parser.parse_args()
                iden = token_decode(args['token'])
                if iden:
                    row = self.model.get_row(args['id'])
                    return {
                        "success": True,
                        "results": row['description']
                    }
                else:
                    raise Exception("Invalid token")
            except Exception as error:
                return {"success": False, "message": str(error)}

    class PGRowSaveMetadata(Resource):

        def __init__(self):
            c = Pages()
            self.model = c.Model()

        def post(self):
            try:
                parser.add_argument('token', type=str)
                parser.add_argument('id', type=str)
                parser.add_argument('metadata', type=str)
                args = parser.parse_args()
                iden = token_decode(args['token'])
                if iden:
                    u = self.model.update_row_metadata(
                        args['id'], args['metadata'])
                    if u:
                        return {
                            "success": True
                        }
                else:
                    raise Exception("Invalid token")
            except Exception as error:
                return {"success": False, "message": str(error)}
