# SIMAR_ADMIN_API
API for SIMAR ADMIN


### O.S. dependencies
```
sudo apt-get install python3
sudo apt-get install python3-pip
sudo apt-get install mysql-client
sudo apt install default-libmysqlclient-dev
```

### Create Virtual environment
```
python3 -m venv /data/apps/simar_admin_api/venv
source venv/bin/activate
deactivate

```

### Python3 dependencies
```
sudo pip3 install passlib
sudo pip3 install flask
sudo pip3 install Flask-WTF
sudo pip3 install flask_restful
sudo pip3 install requests
sudo pip3 install -U flask-cors
sudo pip3 install flask-jwt-extended
sudo pip3 install configparser
sudo pip3 install mysql-connector
sudo pip3 install flask-mysqldb
sudo pip3 install psycopg2
sudo pip3 install bcrypt

```

### When using Virtual environment
```
pip install passlib
pip install flask
pip install Flask-WTF
pip install flask_restful
pip install requests
pip install -U flask-cors
pip install flask-jwt-extended
pip install configparser
pip install mysql-connector
pip install flask-mysqldb
pip install psycopg2
pip install bcrypt
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### How to run
```
python3 app.py
```
### Debian NodeJS, NPM and PM2 setup
```
curl -sL https://deb.nodesource.com/setup_12.x | sudo -E bash -
sudo apt-get install -y nodejs
sudo apt-get install gcc g++ make
sudo npm i -g pm2

```