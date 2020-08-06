from __future__ import print_function
import pickle
import os.path
import base64
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError

from email.mime.text import MIMEText

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]


class GmailAPITools:

    def __init__(self):

        self.from_addr = 'monitoreo.marino@gmail.com'

        cred_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'credentials.json'))

        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    cred_file, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('gmail', 'v1', credentials=creds)

    def create_message(self, to, subject, message_text):
        message = MIMEText(message_text)
        message['to'] = to
        message['from'] = self.from_addr
        message['subject'] = subject
        return {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}

    def create_html_message(self, to, subject, message_text):
        message = MIMEText(message_text, 'html')
        message['to'] = to
        message['from'] = "SIMAR <%s>" % self.from_addr
        message['subject'] = subject
        return {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}

    def send_test_email(self, to_email):
        msg = self.create_message(to_email, "This is a test email.", "This a test message body.")
        self.send_email(msg)

    def send_recovery_email(self, to_email, url):
        subj = "Reestablezca su contraseña."
        body = """<p style="font-family: sans-serif;"><a href="%s">Click aqui</a> para reestablecer su contrasela.</p>""" % url
        msg = self.create_html_message(to_email, subj, body)
        self.send_email(msg)

    def send_activation_email(self, to_email, usrnm, pss, url):
        subj = "Acceso a SIMAR."
        body = """<p style="font-family: sans-serif;">Usuario: {n}</p><p style="font-family: sans-serif;">Contraseña: {p}</p>""".format(u=url, n=usrnm, p=pss)
        msg = self.create_html_message(to_email, subj, body)
        self.send_email(msg)

    def send_email(self, message):
        message = (self.service.users().messages().send(userId='me', body=message)
                   .execute())
        print('Message Id: %s' % message['id'])