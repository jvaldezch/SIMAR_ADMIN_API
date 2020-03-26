# -*- coding: utf-8 -*-
import datetime
import mysql.connector
import urllib.parse
import psycopg2
import bcrypt

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


class AuthModel:

    def __init__(self, db):
        self.db = db

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
                None
        except psycopg2.Error as err:
            self.db.rollback()
            raise Exception(err)

    def update_user_password(self, id_user, n_password):
        try:            
            cur = self.db.connection.cursor()
            cur.execute(
                "UPDATE users SET `password` = '%s' WHERE id = %s;" % (n_password, id_user))
            self.db.connection.commit()
            cur.close()
            return True
        except mysql.connector.Error as err:
            raise Exception(err.message)


    def challenge_email(self, username):
        try:
            cur = self.db.connection.cursor()
            sql = "SELECT * FROM users WHERE email = '%s';" % username
            results = cur.execute(sql)
            if results > 0:
                row = cur.fetchone()
                return row
            else:
                return None
        except mysql.connector.Error as err:
            raise Exception(err.message)

    def add_token(self, id_user, token):
        try:
            cur = self.db.cursor(cursor_factory=RealDictCursor)
            query = """INSERT INTO systems_users_tokens(id_user, token, process) VALUES (%s, '%s', '%s');""" % (id_user, token, 'login')
            cur.execute(query)
            self.db.commit()            
        except psycopg2.Error as err:
            self.db.rollback()
            raise Exception(err)

    def add_recover_token(self, id_user, token):
        try:
            cur = self.db.connection.cursor()
            cur.execute(
                "INSERT INTO tokens(id_user, token, `type`) VALUES (%s, %s, %s);", (id_user, token, 'recovery'))
            self.db.connection.commit()
            cur.close()
            return True
        except mysql.connector.Error as err:
            raise Exception(err.message)

    def delete_token(self, id_user):
        try:
            cur = self.db.cursor(cursor_factory=RealDictCursor)
            query = """DELETE FROM systems_users_tokens AS t WHERE t.id_user = '%s';""" % id_user
            cur.execute(query)
            self.db.commit()
        except psycopg2.Error as err:
            self.db.rollback()
            raise Exception(err)

    def delete_recover_token(self, id_user):
        try:
            cur = self.db.connection.cursor()
            cur.execute(
                "DELETE FROM tokens WHERE id_user = %s AND `type`  = 'recovery';" % id_user)
            self.db.connection.commit()
            cur.close()
        except mysql.connector.Error as err:
            raise Exception(err.message)

    def check_recover_token(self, token):
        try:
            cur = self.db.connection.cursor()
            sql = "SELECT id, id_user FROM tokens WHERE token = '%s' AND `type`  = 'recovery' AND `updated_at` IS NULL;" % token
            results = cur.execute(sql)
            if results > 0:
                row = cur.fetchone()
                cur.close()
                return row
            else:
                cur.close()
                return None
        except mysql.connector.Error as err:
            raise Exception(err.message)

    def update_token(self, id_token):
        try:
            cur = self.db.connection.cursor()
            cur.execute(
                "UPDATE tokens SET `updated_at` = '%s' WHERE id = %s;" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), id_token))
            self.db.connection.commit()
            cur.close()
        except mysql.connector.Error as err:
            raise Exception(err.message)

    def get_user_roles(self, id_user):
        try:
            cur = self.db.connection.cursor()
            results = cur.execute(
                "SELECT role FROM user_roles WHERE id_user = %s;" % id_user)
            if results > 0:
                rows = cur.fetchall()
                cur.close()
                return rows
            cur.close()
            return False
        except mysql.connector.Error as err:
            raise Exception(err.message)


class Login(Resource):

    def __init__(self, db):
        self.model = AuthModel(db)

    def post(self):
        try:
            parser.add_argument('username', type=str)
            parser.add_argument('password', type=str)
            args = parser.parse_args()

            # e_password = sha256_crypt.encrypt(str(args['password']))
            # app.logger.info(e_password)

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

    def __init__(self, db):
        self.model = AuthModel(db)

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

    def __init__(self, db):
        self.model = AuthModel(db)

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

    def __init__(self, db):
        self.model = AuthModel(db)

    def post(self):
        try:
            return {"success": True}
        except Exception as error:
            print(error)
            return {"success": False, "message": str(error)}


class Validate(Resource):

    def __init__(self, db):
        self.model = AuthModel(db)

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


class RestoreToken(Resource):

    def __init__(self, db):
        self.model = AuthModel(db)

    def post(self):
        try:
            parser.add_argument('token', type=str)
            args = parser.parse_args()

            if 'token' in args:
                r = self.model.check_recover_token(args['token'])
                if r:
                    recov = token_decode(args['token'])
                    if (recov['id_user'] == r['id_user']):
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


class ChangePassword(Resource):

    def __init__(self, db):
        self.model = AuthModel(db)

    def post(self):
        try:
            parser.add_argument('token', type=str)
            parser.add_argument('password', type=str)
            args = parser.parse_args()

            if 'token' in args and 'password' in args:
                r = self.model.check_recover_token(args['token'])
                if r:
                    recov = token_decode(args['token'])
                    if (recov['id_user'] == r['id_user']):

                        new_password = sha256_crypt.encrypt(str(args['password']))

                        u = self.model.update_user_password(r['id_user'], new_password)
                        if u:
                            t = self.model.update_token(r['id'])
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


class Recover(Resource):

    def __init__(self, db, frontend_uri):
        self.model = AuthModel(db)
        self.frontend_uri = frontend_uri

    def post(self):
        try:

            parser.add_argument('email', type=str)
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
                            uri = urllib.parse.quote(recover_token)
                            emt = EmailTools()
                            emt.send_recovery_email(
                                args['email'], self.frontend_uri + "/restablecer/" + uri)
                            emt.send_email()

                            return {"success": True}

                        else:
                            raise Exception("Could not add token")
                else:
                    raise Exception("Email not found")
            else:
                raise Exception("Invalid input!")
        except Exception as error:
            print(error)
            return {"success": False, "message": str(error)}
