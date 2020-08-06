# -*- coding: utf-8 -*-
import os
import random
import string
import datetime
import urllib.parse
import psycopg2
import bcrypt
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
from utilities.email_stmp import EmailTools
from utilities.gmail_tools import GmailAPITools

parser = reqparse.RequestParser()


def token_decode(token):
    de = decode_token(token)
    if 'identity' in de:
        iden = de['identity']
        return iden
    else:
        return False


class AuthModel:

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
            raise Exception('Could not connect to db ', err)

    def challenge_user(self, username):
        try:
            cur = self.db.cursor(cursor_factory=RealDictCursor)
            query = """SELECT * FROM systems_users AS u WHERE u.username = '%s';""" % username
            cur.execute(query)
            row = cur.fetchone()
            cur.close()
            if row:
                return row
            else:
                return None
        except psycopg2.Error as err:
            self.db.rollback()
            raise Exception(err)

    def update_user_password(self, id_user, n_password):
        try:
            cur = self.db.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                "UPDATE systems_users SET password = '{p}' WHERE id = {i};".format(p=n_password, i=id_user))
            self.db.commit()
            cur.close()
            return True
        except psycopg2.Error as err:
            self.db.rollback()
            raise Exception(err)

    def challenge_email(self, email):
        try:
            cur = self.db.cursor(cursor_factory=RealDictCursor)
            query = "SELECT id FROM systems_users WHERE email = '{e}';".format(e=email)
            cur.execute(query)
            row = cur.fetchone()
            cur.close()
            if row:
                return row
            else:
                return None
        except psycopg2.Error as err:
            self.db.rollback()
            raise Exception(err)

    def add_token(self, id_user, token):
        try:
            n = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur = self.db.cursor(cursor_factory=RealDictCursor)
            query = """INSERT INTO systems_users_tokens(id_user, token, process, created_at) VALUES ({i}, '{t}', '{p}', '{d}');""".format(i=id_user, t=token, p='login', d=n)
            cur.execute(query)
            self.db.commit()
            cur.close()
        except psycopg2.Error as err:
            self.db.rollback()
            raise Exception(err)

    def add_token_type(self, id_user, token, type):
        try:
            n = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur = self.db.cursor(cursor_factory=RealDictCursor)
            query = """INSERT INTO systems_users_tokens(id_user, token, process, created_at) VALUES ({i}, '{t}', '{p}', '{d}');""".format(i=id_user, t=token, p=type, d=n)
            cur.execute(query)
            self.db.commit()
            cur.close()
            return True
        except psycopg2.Error as err:
            self.db.rollback()
            raise Exception(err)

    def add_recover_token(self, id_user, token):
        try:
            n = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur = self.db.cursor(cursor_factory=RealDictCursor)
            query = "INSERT INTO systems_users_tokens(id_user, token, process, created_at) VALUES ({i}, '{t}', '{p}', '{d}');".format(i=id_user, t=token, p='recovery', d=n)
            cur.execute(query)
            self.db.commit()
            cur.close()
            return True
        except psycopg2.Error as err:
            self.db.rollback()
            raise Exception(err)

    def add_user(self, email, name, last_name, username, password):
        try:
            d = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur = self.db.cursor(cursor_factory=RealDictCursor)
            query = "INSERT INTO systems_users(email, name, last_name, created_at, role, username, password, profile_img) VALUES ('{e}', '{n}', '{l}', '{d}', '{r}', '{u}', '{p}', '{m}') RETURNING id;".format(e=email, n=name, l=last_name, d=d, r='user', u=username, p=password, m='/profiles/users/profile-default.jpg')
            cur.execute(query)
            self.db.commit()
            i = cur.fetchone()
            cur.close()
            return i['id']
        except psycopg2.Error as err:
            self.db.rollback()
            raise Exception(err)

    def add_user_data(self, id_user, institute):
        try:
            cur = self.db.cursor(cursor_factory=RealDictCursor)
            query = "INSERT INTO systems_users_data(id_user, instituto) VALUES ('{i}', '{n}');".format(i=id_user, n=institute)
            cur.execute(query)
            self.db.commit()
            cur.close()
            return True
        except psycopg2.Error as err:
            self.db.rollback()
            raise Exception(err)

    def delete_token(self, id_user):
        try:
            cur = self.db.cursor(cursor_factory=RealDictCursor)
            query = """DELETE FROM systems_users_tokens AS t WHERE t.id_user = '{i}';""".format(i=id_user)
            cur.execute(query)
            self.db.commit()
        except psycopg2.Error as err:
            self.db.rollback()
            raise Exception(err)

    # def delete_recover_token(self, id_user):
    #     try:
    #         cur = self.db.connection.cursor()
    #         cur.execute(
    #             "DELETE FROM tokens WHERE id_user = %s AND `type`  = 'recovery';" % id_user)
    #         self.db.connection.commit()
    #         cur.close()
    #     except mysql.connector.Error as err:
    #         raise Exception(err.message)

    def check_token_type(self, id_user, token, token_type):
        try:
            cur = self.db.cursor(cursor_factory=RealDictCursor)
            query = "SELECT id, id_user FROM systems_users_tokens WHERE id_user = {i} AND token = '{t}' AND process = '{p}';".format(i=id_user, t=token, p=token_type)
            cur.execute(query)
            row = cur.fetchone()
            cur.close()
            if row:
                return row
            return None
        except psycopg2.Error as err:
            self.db.rollback()
            raise Exception(err)

    def delete_token(self, id_token):
        try:
            cur = self.db.cursor(cursor_factory=RealDictCursor)
            query = "DELETE FROM systems_users_tokens WHERE id = {i};".format(i=id_token)
            cur.execute(query)
            self.db.commit()
            cur.close()
        except psycopg2.Error as err:
            self.db.rollback()
            raise Exception(err)

    # def get_user_roles(self, id_user):
    #     try:
    #         cur = self.db.connection.cursor()
    #         results = cur.execute(
    #             "SELECT role FROM user_roles WHERE id_user = %s;" % id_user)
    #         if results > 0:
    #             rows = cur.fetchall()
    #             cur.close()
    #             return rows
    #         cur.close()
    #         return False
    #     except mysql.connector.Error as err:
    #         raise Exception(err.message)


class Login(Resource):

    def __init__(self):
        self.model = AuthModel()

    def post(self):
        try:
            parser.add_argument('username', type=str)
            parser.add_argument('password', type=str)
            args = parser.parse_args()

            u = self.model.challenge_user(args['username'])
            if u:                
                v = bcrypt.checkpw(args['password'].encode(), u['password'].encode())
                if v:
                    self.model.delete_token(u['id'])
                    
                    landing = None
                    if u['role'] == 'admin':
                        landing = '/admin/dashboard'

                    usr_data = {
                        'id_user': u['id'],
                        'email': u['email'],
                        'roles': u['role'],
                        'profile_img': u['profile_img'],
                    }
                    expires = datetime.timedelta(days=365)

                    access_token = create_access_token(
                        identity=usr_data, expires_delta=expires)

                    self.model.add_token(u['id'], access_token)

                    return {"success": True, "landing": landing, "profile_img": u['profile_img'], "token": access_token}

                else:
                    raise Exception("Invalid password")
            else:
                raise Exception("User not found")
        except Exception as error:            
            return {"success": False, "message": str(error)}


class Roles(Resource):

    def __init__(self):
        self.model = AuthModel()

    def post(self):
        try:
            token = str(request.headers.get(
                'Authorization')).replace("Bearer ", "")

            iden = token_decode(token)
            if iden:
                roles = self.model.get_user_roles(iden['id_user'])
                r = []
                for key in roles:
                    r.append(key['role'])

                return {"success": True, 'roles': r}
            else:
                raise Exception("Invalid token")
        except Exception as error:
            return {"success": False, "message": str(error)}


class Logout(Resource):

    def __init__(self):
        self.model = AuthModel()

    def post(self):
        try:
            token = str(request.headers.get(
                'Authorization')).replace("Bearer ", "")

            iden = token_decode(token)
            if iden:
                self.model.delete_token(iden['id_user'])

            return {"success": True}
        except Exception as error:
            print(error)
            return {"success": False, "message": str(error)}


class Update(Resource):

    def __init__(self):
        self.model = AuthModel()

    def post(self):
        try:
            return {"success": True}
        except Exception as error:
            print(error)
            return {"success": False, "message": str(error)}


class Validate(Resource):

    def __init__(self):
        self.model = AuthModel()

    def post(self):
        try:          
            parser.add_argument('token', type=str)
            args = parser.parse_args()
            iden = token_decode(args['token'])
            if iden:
                return {
                    "success": True, 
                    "email": iden['email'],
                    "profile_img": iden['profile_img'],
                }
            else:
                raise Exception("Invalid token")                
        except Exception as error:
            return {"success": False, "message": str(error)}


class ValidateToken(Resource):

    def __init__(self):
        self.model = AuthModel()

    def post(self):
        try:
            parser.add_argument('token', type=str)
            parser.add_argument('type', type=str)
            args = parser.parse_args()
            iden = token_decode(args['token'])
            if 'token' in args:
                if args['token'] != '':
                    if iden:
                        r = self.model.check_token_type(iden['id_user'], args['token'], args['type'])
                        if r:
                            return {"success": True}
                        else:
                            raise Exception("Token has expired or it is not valid")
                    else:
                        raise Exception("Invalid token")
            raise Exception("No token")
        except Exception as error:
            return {"success": False, "message": str(error)}


class RestoreToken(Resource):

    def __init__(self):
        self.model = AuthModel()

    def post(self):
        try:
            parser.add_argument('token', type=str)
            args = parser.parse_args()

            if 'token' in args:
                r = self.model.check_recover_token(args['token'])
                if r:
                    recov = token_decode(args['token'])
                    if recov['id_user'] == r['id_user']:
                        return {"success": True}
                    else:
                        raise Exception("Invalid token")
                else:
                    raise Exception("Invalid token")
            else:
                return {"success": False}
        except Exception as error:
            print(error)
            return {"success": False, "message": str(error)}


class Register(Resource):

    def __init__(self, base_url):
        self.model = AuthModel()
        self.base_url = base_url

    def randon_password(self, size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def post(self):
        try:
            parser.add_argument('n_name', type=str)
            parser.add_argument('n_lastname', type=str)
            parser.add_argument('n_institute', type=str)
            parser.add_argument('n_email', type=str)
            parser.add_argument('n_usrnm', type=str)
            args = parser.parse_args()

            if args['n_name'] and args['n_lastname'] and args['n_institute'] and args['n_email'] and args['n_usrnm']:
                u = self.model.challenge_user(args['n_usrnm'])
                if u:
                    raise Exception("Nombre de usuario ya registrado.")
                e = self.model.challenge_email(args['n_email'])
                if e:
                    raise Exception("Ya existe un usuario con ese email registrado.")

                if not u and not e:

                    pss = self.randon_password(size=10)
                    pss_e = bcrypt.hashpw(str(pss).encode('utf-8'), bcrypt.gensalt())

                    id_user = self.model.add_user(args['n_email'], args['n_name'], args['n_lastname'], args['n_usrnm'], pss_e.decode('utf-8'))
                    if id_user:
                        self.model.add_user_data(id_user, args['n_institute'])

                        usr_data = {
                            'id_user': id_user,
                            'email': args['n_email'],
                            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }

                        expires = datetime.timedelta(days=2)

                        register_token = create_access_token(identity=usr_data, expires_delta=expires)

                        r = self.model.add_token_type(id_user, register_token, 'register')
                        if r:
                            uri = urllib.parse.quote_plus(register_token)
                            emt = GmailAPITools()
                            emt.send_activation_email(args['n_email'], args['n_usrnm'], pss, self.base_url + "activar/" + uri)

                            return {"success": True, "message": "Hemos enviado un mensaje a su correo eletrónico. Complete el registro activando su usario activandolo."}
                        else:
                            raise Exception("No se pudo agregar token")

                    raise Exception("No se pudo agregar usuario")

                raise Exception("Unknown exception found")

            return {"success": False}

        except Exception as error:
            return {"success": False, "message": str(error)}


class ActivateUser(Resource):

    def __init__(self):
        self.model = AuthModel()

    def post(self):
        try:
            parser.add_argument('token', type=str)
            args = parser.parse_args()

            return {"success": False}

        except Exception as error:
            print(error)
            return {"success": False, "message": str(error)}


class ChangePassword(Resource):

    def __init__(self):
        self.model = AuthModel()

    def post(self):
        try:
            parser.add_argument('token', type=str)
            parser.add_argument('upwd', type=str)
            args = parser.parse_args()

            iden = token_decode(args['token'])

            if 'token' in args and 'upwd' in args:

                r = self.model.check_token_type(iden['id_user'], args['token'], 'recovery')
                if r:
                    recov = token_decode(args['token'])
                    if recov['id_user'] == r['id_user']:
                        new_password = bcrypt.hashpw(str(args['upwd']).encode('utf-8'), bcrypt.gensalt())

                        u = self.model.update_user_password(r['id_user'], new_password.decode('utf-8'))
                        if u:
                            self.model.delete_token(r['id'])
                            return {"success": True}
                        else:
                            raise Exception("Unable to update password")
                    else:
                        raise Exception("Invalid token")
                else:
                    raise Exception("Invalid token")
            else:
                raise Exception("Invalid input!")

        except Exception as error:
            print(error)
            return {"success": False, "message": str(error)}


class Recovery(Resource):

    def __init__(self, base_url):
        self.model = AuthModel()
        self.base_url = base_url

    def post(self):
        try:

            parser.add_argument('email', type=str)
            parser.add_argument('lang', type=str)
            args = parser.parse_args()

            if 'email' in args:
                u = self.model.challenge_email(args['email'])
                if u:
                    usr_data = {
                        'id_user': u['id'],
                        'email': args['email'],
                        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    expires = datetime.timedelta(days=2)

                    recover_token = create_access_token(
                        identity=usr_data, expires_delta=expires)

                    if recover_token:
                        r = self.model.add_recover_token(
                            u['id'], recover_token)
                        if r:
                            uri = urllib.parse.quote_plus(recover_token)
                            rec_url = self.base_url + "restablecer/" + uri

                            emt = GmailAPITools()
                            emt.send_recovery_email(
                                args['email'], rec_url)

                            if args['lang'] == 'es':
                                m = "Hemos enviado un email para restablecer su contraseña."
                            else:
                                m = "We have sent an email to reset your password."

                            return {"success": True, "message": m}

                        else:
                            raise Exception("Could not add token")
                else:
                    raise Exception("Email not found")
            else:
                raise Exception("Invalid input!")
        except Exception as error:
            print(error)
            return {"success": False, "message": str(error)}
