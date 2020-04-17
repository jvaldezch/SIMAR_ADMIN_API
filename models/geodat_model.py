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


class GeoDat:
    
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
                self.db = psycopg2.connect(database=dbname, user=user, password=passwd, host=host)
            except Exception as err:
                print(str(err), ' could not connect to db')
                sys.exit()

        def get_total(self, category_id, search=None):
            try:                
                cur = self.db.cursor(cursor_factory=RealDictCursor)
                query = """SELECT count(*) AS total FROM systems_products AS s WHERE category_id = %s;""" % category_id
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

        def get_rows(self, category_id, c_page=1, p_size=10, search=None):
            try:
                cur = self.db.cursor(cursor_factory=RealDictCursor)
                query = """SELECT * FROM systems_products AS s WHERE category_id = %s ORDER BY "name" ASC LIMIT %s OFFSET %s;""" % (category_id, p_size, (c_page - 1) * p_size)
                cur.execute(query)
                rows = cur.fetchall()
                cur.close()
                if rows:
                    arr = []
                    for row in rows:
                        arr.append({
                            'id': row['id'],
                            'name': row['name'],
                            'name_en': row['name_en'],
                            'order': row['order'],
                            'visible': row['visible'],
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
                query = """SELECT * FROM systems AS s WHERE s.id = %s;""" % id
                cur.execute(query)
                row = cur.fetchone()
                cur.close()
                if row:
                    return {
                        'id': row['id'],
                        'name': row['name'],
                        'name_en': row['name_en'],
                        'order': row['order'],
                        'visible': row['visible'],
                        'image': row['image'],
                        'metadata_img': row['metadata_img'],
                        'description': row['description'],
                    }
                else:
                    return None
            except psycopg2.Error as err:
                self.db.rollback()
                raise Exception(err)


    class GRows(Resource):

        def __init__(self):
            c = GeoDat()
            self.model = c.Model()

        def post(self):
            try:
                parser.add_argument('token', type=str)
                parser.add_argument('currentPage', type=int)
                parser.add_argument('pageSize', type=int)
                parser.add_argument('search', type=str)
                parser.add_argument('categoryId', type=int)
                args = parser.parse_args()
                iden = token_decode(args['token'])
                if iden:
                    rows = self.model.get_rows(args['categoryId'], c_page=args['currentPage'], p_size=args['pageSize'],
                                               search=args['search'])
                    return {
                        "success": True,
                        "email": iden['email'],
                        "profile_img": iden['profile_img'],
                        "rows": rows,
                        "total": self.model.get_total(args['categoryId'], search=args['search'])
                    }
                else:
                    raise Exception("Invalid token")
            except Exception as error:
                return {"success": False, "message": str(error)}


    class GRow(Resource):

        def __init__(self):
            c = GeoDat()
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
            
