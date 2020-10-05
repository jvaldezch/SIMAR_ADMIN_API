# -*- coding: utf-8 -*-
import os
import sys
import datetime
import urllib.parse
import psycopg2
import configparser
import pytz

from psycopg2.extras import RealDictCursor
from passlib.hash import sha256_crypt

from flask import request

from flask_restful import Resource, Api, reqparse
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, decode_token
)

from models.token_model import TokenModel

mctz = pytz.timezone('America/Mexico_City')

parser = reqparse.RequestParser()


def token_decode(token):
    de = decode_token(token)
    if 'identity' in de:
        iden = de['identity']
        return iden
    else:
        return False


class Stats:
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

        def get_by_day(self, day):
            try:
                cur = self.db.cursor(cursor_factory=RealDictCursor)
                sql = """SELECT * FROM ocean_color_satmo_nc n WHERE n.created::DATE = '{d}';""".format(d=day)
                cur.execute(sql)
                rows = cur.fetchall()
                cur.close()
                if rows:
                    arr = []
                    for r in rows:
                        arr.append({
                            'id': r['rid'],
                            'composition': r['composition'],
                            'sensor': r['sensor'],
                            'filename': r['filename'],
                            'product_date': r['product_date'].strftime("%Y-%m-%d"),
                            'product_end': r['product_end'].strftime("%Y-%m-%d"),
                        })
                    return arr
                else:
                    return []
            except psycopg2.Error as err:
                self.db.rollback()
                raise Exception(err)

        def get_stats(self, today, yestarday):
            try:
                cur = self.db.cursor(cursor_factory=RealDictCursor)
                sql = """SELECT
                        to_char(s.tag, 'yyyy-mm-dd') AS label,
                        COUNT (T . rid) AS y,
			            json_object(array_agg(T.rid)::text[],array_agg(T.composition)::text[]) AS detail
                    FROM
                        (
                            SELECT
                                generate_series (
                                    MIN ('{y}') :: DATE,
                                    MAX ('{t}') :: DATE,
                                    INTERVAL '1 day'
                                ) :: DATE AS tag
                            FROM
                                ocean_color_satmo_nc T
                        ) s
                    LEFT JOIN ocean_color_satmo_nc T ON T .created :: DATE = s.tag
                    WHERE T.composition IS NOT NULL
                    GROUP BY
                        1
                    ORDER BY
                        1;""".format(y=yestarday, t=today)
                cur.execute(sql)
                rows = cur.fetchall()
                cur.close()
                if rows:
                    return rows
                else:
                    return []
            except psycopg2.Error as err:
                self.db.rollback()
                raise Exception(err)

    class Total(Resource):

        def __init__(self):
            c = Stats()
            self.model = c.Model()

        def post(self):
            try:
                parser.add_argument('token', type=str)
                parser.add_argument('y', type=str)
                parser.add_argument('t', type=str)
                args = parser.parse_args()
                iden = token_decode(args['token'])
                if iden:
                    rows = self.model.get_stats(args['t'], args['y'])
                    return {
                        "success": True, "results": rows
                    }
                else:
                    raise Exception("Invalid token")
            except Exception as error:
                print(error)
                return {"success": False, "message": str(error)}

    class TotalDiario(Resource):

        def __init__(self):
            c = Stats()
            self.model = c.Model()

        def post(self):
            try:
                parser.add_argument('token', type=str)
                parser.add_argument('today', type=str)
                args = parser.parse_args()
                iden = token_decode(args['token'])
                if iden:
                    rows = self.model.get_by_day(args['today'])
                    return {
                        "success": True, "results": rows
                    }
                else:
                    raise Exception("Invalid token")
            except Exception as error:
                print(error)
                return {"success": False, "message": str(error)}
