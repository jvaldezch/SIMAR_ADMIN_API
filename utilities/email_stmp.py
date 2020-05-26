# -*- coding: utf-8 -*-
import os
import smtplib
import configparser

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailTools:

    def __init__(self):

        self.msg = None

        config = configparser.ConfigParser()

        dirname = os.path.abspath(os.path.dirname(__file__))
        config_path = os.path.join(dirname, '../.config.ini')
        config.read(config_path)

        self.from_addr = config.get('smtp', 'from')
        self.smtp_server = config.get('smtp', 'smtp')
        self.smtp_port = config.get('smtp', 'port')
        self.from_pass = config.get('smtp', 'pass')

        self.msg = MIMEMultipart()

    def send_test_email(self, to_email):

        self.msg['From'] = "SIMAR <%s>" % self.from_addr
        self.msg['To'] = to_email
        self.msg['Subject'] = "Email de prueba."

        self.msg.attach(MIMEText("""<p style="font-family: sans-serif;">Prueba de email.</p>""", 'html'))

    def send_recovery_email(self, to_email, url):

        self.msg['From'] = "SIMAR <%s>" % self.from_addr
        self.msg['To'] = to_email
        self.msg['Subject'] = "Reestablezca su contraseña."

        self.msg.attach(MIMEText("""<p style="font-family: sans-serif;"><a href="%s">Click aqui</a> para reestablecer su contrasela.</p>""" % url, 'html'))

    def send_activation_email(self, to_email, usrnm, pss, url):

        self.msg['From'] = "SIMAR <%s>" % self.from_addr
        self.msg['To'] = to_email
        self.msg['Subject'] = "Acceso a SIMAR."

        self.msg.attach(MIMEText("""<p style="font-family: sans-serif;">Usuario: {n}</p><p style="font-family: sans-serif;">Contraseña: {p}</p>""".format(u=url, n=usrnm, p=pss), 'html'))

    def send_email(self):
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        # server.ehlo()
        server.login(self.from_addr, self.from_pass)

        server.sendmail(self.from_addr, self.msg['To'], self.msg.as_string())
        # server.quit()
        server.close()


