from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from datetime import datetime

import psycopg2, json, base64, uuid

db_config_file = open('config.json')
db_config = json.load(db_config_file)

def fetch_emails(gmail_creds):

    try:
        # instantiate gmail service
        service = build('gmail', 'v1', credentials=gmail_creds)

        # first use gmail message listing api to fetch all the message ids
        results = service.users().messages().\
            list(userId='me', maxResults=500, labelIds=["INBOX", "CATEGORY_PERSONAL"]).execute()
        messages = results.get('messages', [])
        nextPageToken = results.get('nextPageToken', '')

        # nextPageToken is used to access message ids from the next page
        while nextPageToken:
            nextResults = service.users().messages().list(userId='me', pageToken=nextPageToken, maxResults=500, labelIds=["INBOX", "CATEGORY_PERSONAL"]).execute()
            messages.extend(nextResults.get('messages',[]))
            nextPageToken = nextResults.get('nextPageToken', '')

        message_count, total_messages = 0, len(messages)

        # fetch details of messages using message ids
        for message in messages:
            message_id = message["id"]
            message_count += 1
            message_result = service.users().messages().get(userId='me', id=message_id).execute()
            message_date = datetime.fromtimestamp(int(message_result['internalDate']) / 1000)

            message_result_payload = message_result['payload']
            message_headers = message_result_payload['headers']
            message_from, message_subject = '', ''

            for header in message_headers:
                if header['name'] == 'From':
                    message_from = header['value']

                if header['name'] == 'Subject':
                    message_subject = header['value']

            message_content = ''
            if "parts" in message_result_payload:
                for part in message_result_payload["parts"]:
                    if 'body' in part and 'data' in part['body']:
                        message_content += base64.urlsafe_b64decode(part['body']['data']).decode()
            else:
                if 'body' in message_result_payload and 'data' in message_result_payload['body']:
                    message_content += base64.urlsafe_b64decode(message_result_payload['body']['data']).decode()

            # instantiate postgres connection and insert the emails onto the db
            postgres_connection = psycopg2.connect(
                host=db_config["db_server"],
                database=db_config["db_name"],
                user=db_config["db_username"],
                password=db_config["db_password"])

            cursor = postgres_connection.cursor()
            cursor.execute("""
            INSERT INTO emails (id, message_id, sender_email, date, message_content, subject) 
            VALUES(%s, %s, %s, %s, %s, %s)""",\
            (str(uuid.uuid4()), message['id'], message_from, message_date, message_content, message_subject))

        postgres_connection.commit()
        cursor.close()
        postgres_connection.close()


    except HttpError as error:
        print(f'An error occurred: {error}')