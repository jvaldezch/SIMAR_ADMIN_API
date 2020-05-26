# -*- coding: utf-8 -*-

import os
import sys
import psycopg2

import configparser

from flask import Flask, render_template, flash, redirect, url_for, session, logging, request, \
    jsonify, send_from_directory
from flask_cors import CORS

# from wtforms import Form, StringField, TextAreaField, PasswordField, validators
# from passlib.hash import sha256_crypt
from functools import wraps
import requests

from flask_restful import Resource, Api, reqparse
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, decode_token
)

from models.home_model import Root, ApiRoot
from models.auth_model import Login, Logout, Roles, Update, Validate, Recovery, RestoreToken, \
    ChangePassword, ValidateToken, Register, ActivateUser

from models.sistemas_model import Systems
from models.categorias_model import Categories
from models.subcategorias_model import SubCategories
from models.productos_model import Products
from models.geodat_model import GeoDat
from models.usuarios_model import Users
from models.imagenes_model import Images
from models.actividad_model import Activity
from models.paginas_model import Pages

parser = reqparse.RequestParser()

app = Flask(__name__)
api = Api(app)
cors = CORS(app)

config = configparser.ConfigParser()

dirname = os.path.abspath(os.path.dirname(__file__))
config_path = os.path.join(dirname, '.config.ini')
config.read(config_path)

try:
    secret_key = config.get('secret', 'key')

    app.config['JWT_SECRET_KEY'] = secret_key
    jwt = JWTManager(app)

    host = config.get('dbsettings', 'db_host')
    user = config.get('dbsettings', 'db_user')
    passwd = config.get('dbsettings', 'db_passwd')
    dbname = config.get('dbsettings', 'db_dbname')
    db = psycopg2.connect(database=dbname, user=user, password=passwd, host=host)

    base_url = config.get('env', 'base_url')
    admin_url = config.get('env', 'admin_url')
    vtiles_url = config.get('env', 'vtiles_url')
    vitles_cache = config.get('env', 'vitles_cache')
    download_uri = config.get('env', 'download_uri')
    l_port = config.get('env', 'port')

except Exception as err:
    print(str(err), ' could not connect to db')
    sys.exit()


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


api.add_resource(Root, '/')
api.add_resource(ApiRoot, '/api')

api.add_resource(Login, '/api/login')
api.add_resource(Logout, '/api/logout')
api.add_resource(Update, '/api/update')
api.add_resource(Validate, '/api/validate')
api.add_resource(ValidateToken, '/api/validate-token')
api.add_resource(Roles, '/api/roles')
api.add_resource(Recovery, '/api/recovery',
                 resource_class_kwargs={'base_url': base_url})
api.add_resource(RestoreToken, '/api/restore-token')
api.add_resource(ChangePassword, '/api/change-password')
api.add_resource(Register, '/api/register',
                 resource_class_kwargs={'base_url': base_url})
api.add_resource(ActivateUser, '/api/activate-user')

systems = Systems()

api.add_resource(systems.Rows, '/api/sistemas')
api.add_resource(systems.Row, '/api/sistema')
api.add_resource(systems.RowMetadata, '/api/obtener-metadata-sistema')
api.add_resource(systems.RowSave, '/api/guardar-sistema')
api.add_resource(systems.RowSaveMetadata, '/api/guardar-metadata-sistema')
api.add_resource(systems.RowVisible, '/api/sistema-visible')

cats = Categories()

api.add_resource(cats.CRows, '/api/categorias')
api.add_resource(cats.CRow, '/api/categoria')
api.add_resource(cats.CRowMetadata, '/api/obtener-metadata-categoria')
api.add_resource(cats.CRowSave, '/api/guardar-categoria')
api.add_resource(cats.CRowSaveMetadata, '/api/guardar-metadata-categoria')
api.add_resource(cats.CRowVisible, '/api/categoria-visible')

scats = SubCategories()

api.add_resource(scats.SCRows, '/api/subcategorias')
api.add_resource(scats.SCRow, '/api/subcategoria')
api.add_resource(scats.SCRowMetadata, '/api/obtener-metadata-subcategoria')
api.add_resource(scats.SCRowSave, '/api/guardar-subcategoria')
api.add_resource(scats.SCRowSaveMetadata, '/api/guardar-metadata-subcategoria')
api.add_resource(scats.SCRowVisible, '/api/subcategoria-visible')
api.add_resource(scats.SCRowActive, '/api/subcategoria-activo')

prods = Products()

api.add_resource(prods.PRows, '/api/productos')
api.add_resource(prods.PRow, '/api/producto')
api.add_resource(prods.PRowMetadata, '/api/obtener-metadata-producto')
api.add_resource(prods.PRowSave, '/api/guardar-producto')
api.add_resource(prods.PRowSaveMetadata, '/api/guardar-metadata-producto')
api.add_resource(prods.PRowVisible, '/api/producto-visible')
api.add_resource(prods.PRowActive, '/api/producto-activo')

prods = GeoDat()

api.add_resource(prods.GRows, '/api/geodat')
api.add_resource(prods.GRow, '/api/vectortile')

usrs = Users()

api.add_resource(usrs.URows, '/api/usuarios')
api.add_resource(usrs.URow, '/api/usuario')

act = Activity()

api.add_resource(act.ARows, '/api/actividades')

imgs = Images()

api.add_resource(imgs.IRows, '/api/imagenes')
api.add_resource(imgs.IRow, '/api/imagen')

pgs = Pages()

api.add_resource(pgs.PGRows, '/api/paginas')
api.add_resource(pgs.PGRow, '/api/pagina')
api.add_resource(pgs.PGRowMetadata, '/api/obtener-metadata-pagina')
api.add_resource(pgs.PGRowSaveMetadata, '/api/guardar-metadata-pagina')

if __name__ == '__main__':
    app.secret_key = secret_key
    app.run(host='0.0.0.0', debug=True, port=l_port)
