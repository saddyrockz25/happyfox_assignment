import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# scope is instantiate as modify and not as readonly so as to allow modification of gmail messages
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def authenticate():
    creds = None

    # see if token.json is available and has the valid credentials
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # if not, request for authorization from the user for the project by redirecting to gmail
    # this happens only for the first time, where token.json is created after user
    # authorizes the project to access gmail
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds