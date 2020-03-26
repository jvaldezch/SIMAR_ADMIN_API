# -*- coding: utf-8 -*-

class TokenModel:

    def __init__(self, db):
        self.db = db

    def add_token(self, id_user, token):
        cur = self.db.connection.cursor()
        cur.execute(
            "INSERT INTO tokens(id_user, token) VALUES (%s, %s, %s);", (id_user, token, 'access'))
        self.db.connection.commit()
        cur.close()

    def add_recover_token(self, id_user, token):
        cur = self.db.connection.cursor()
        cur.execute(
            "INSERT INTO tokens(id_user, token, type) VALUES (%s, %s, %s);", (id_user, token, 'recovery'))
        self.db.connection.commit()
        cur.close()

    def delete_token(self, id_user):
        cur = self.db.connection.cursor()
        cur.execute("DELETE FROM tokens WHERE id_user = %s;" % id_user)
        self.db.connection.commit()
        cur.close()

    def delete_recover_token(self, id_user):
        cur = self.db.connection.cursor()
        cur.execute("DELETE FROM tokens WHERE id_user = %s AND type;" % id_user)
        self.db.connection.commit()
        cur.close()