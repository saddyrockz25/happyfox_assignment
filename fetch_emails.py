from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from datetime import datetime

import psycopg2, json, base64, uuid
import concurrent.futures, traceback

db_config_file = open('config.json')
db_config = json.load(db_config_file)

gmail_creds = ''

# gmail message listing api to fetch all the message ids, each record contains only brief details
def fetch_messages_list():

    # instantiate gmail service
    global gmail_creds
    gmail_service = build('gmail', 'v1', credentials=gmail_creds)

    results = gmail_service.users().messages(). \
        list(userId='me', maxResults=500, labelIds=["INBOX", "CATEGORY_PERSONAL"]).execute()
    messages = results.get('messages', [])
    nextPageToken = results.get('nextPageToken', '')

    # nextPageToken is used to access message ids from the next page
    while nextPageToken:
        nextResults = gmail_service.users().messages().list(userId='me', pageToken=nextPageToken, maxResults=500, \
                                                      labelIds=["INBOX", "CATEGORY_PERSONAL"]).execute()
        messages.extend(nextResults.get('messages', []))
        nextPageToken = nextResults.get('nextPageToken', '')

    return messages

# call the message get api to get complete detail for each message
def fetch_message_details(message):

    # instantiate gmail service
    global gmail_creds
    gmail_service = build('gmail', 'v1', credentials=gmail_creds)

    # fetch message details using the message get api
    message_id = message['id']
    message_result = gmail_service.users().messages().get(userId='me', id=message_id).execute()
    message_date = datetime.fromtimestamp(int(message_result['internalDate']) / 1000)

    # process the payload to get sender email, subject and message body
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

    return (message_id, message_date, message_from, message_subject, message_content)



def fetch_emails(input_gmail_creds):

    try:
        # instantiate postgres connection and insert the emails onto the db
        postgres_connection = psycopg2.connect(
            host=db_config["db_server"],
            database=db_config["db_name"],
            user=db_config["db_username"],
            password=db_config["db_password"])

        cursor = postgres_connection.cursor()

        global gmail_creds
        gmail_creds = input_gmail_creds

        # fetch list of messages, each message contains only brief details
        print("Getting all messages...")
        messages = fetch_messages_list()

        # for each message, fetch complete details using multi-threading
        print("Getting all message details...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            message_objects = executor.map(fetch_message_details, messages)

        print("Adding messages to db...")
        for message_object in message_objects:
            message_id, message_date, message_from, message_subject, message_content = message_object[0], \
            message_object[1], message_object[2], message_object[3], message_object[4]

            # add all data to database
            cursor.execute("""
            INSERT INTO emails (id, message_id, sender_email, date, message_content, subject)
            VALUES(%s, %s, %s, %s, %s, %s)""",\
            (str(uuid.uuid4()), message_id, message_from, message_date, message_content, message_subject))

        postgres_connection.commit()
        cursor.close()
        postgres_connection.close()

        print("End of process !")
    except HttpError as error:
        print(f'An error occurred: {error}')