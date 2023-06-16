from googleapiclient.discovery import build

import json, math
from datetime import datetime
from sqlalchemy import create_engine

import pandas as pd

db_config_file = open('config.json')
db_config = json.load(db_config_file)

# Function to modify emails in gmail based on rules in the json file
def modify_emails(gmail_creds):
    email_rules_file = open('email_rules.json')
    rules = json.load(email_rules_file)

    time_unit_map = {
        "days":1,
        "months":30
    }

    # instantiate postgres connection
    postgres_engine = create_engine("postgresql://" + db_config["db_username"] + ":" + \
    db_config["db_password"] + "@" + db_config["db_server"] + ":" + \
    db_config["db_port"] + "/" + db_config["db_name"])

    with postgres_engine.connect() as connection:

        # read all data initially using pandas
        # pandas is used for better filtering capabilities
        emails_df = pd.read_sql("select * from emails", connection)

        for rule_name in rules:

            # capture the global predicate for the rule - all/any
            global_predicate = list(rules[rule_name].keys())[0]

            for individual_rule in rules[rule_name][global_predicate]:
                rule_key = individual_rule["field"]
                rule_predicate = individual_rule["predicate"]
                rule_value = individual_rule["value"]

                # Date query is handled separately since it has different predicates - less_than/greater_than
                if rule_key == "date_received":

                    # for date, the value is stored as a space separated value -  "3 days",
                    rule_time_value = rule_value.split()[0]
                    rule_time_unit = rule_value.split()[1]

                    # compute the requisite start and end dates
                    today = datetime.now()
                    end_date = str(today.date())
                    start_date = str(datetime.fromtimestamp(math.floor(today.timestamp()) - \
                    (int(rule_time_value) * time_unit_map[rule_time_unit] * 86400)).date())

                    # build the query depending on the predicate
                    if rule_predicate == "less_than":
                        date_query = (emails_df["date"].dt.strftime("%Y-%m-%d %H:%M:%S") > start_date) & \
                                     (emails_df["date"].dt.strftime("%Y-%m-%d %H:%M:%S") < end_date)
                    else:
                        date_query = (emails_df["date"].dt.strftime("%Y-%m-%d %H:%M:%S") < start_date)
                else:
                    # similarly build queries for sender_email, subject and message content depending on predicate
                    if rule_predicate == "contains":
                        if rule_key == "from":
                            sender_email_query = emails_df["sender_email"].str.contains(rule_value)
                        elif rule_key == "subject":
                            subject_query = emails_df["subject"].str.contains(rule_value)
                        else:
                            message_query = emails_df["message_content"].str.contains(rule_value)
                    elif rule_predicate == "does_not_contain":
                        if rule_key == "from":
                            sender_email_query = ~emails_df["sender_email"].str.contains(rule_value)
                        elif rule_key == "subject":
                            subject_query = ~emails_df["subject"].str.contains(rule_value)
                        else:
                            message_query = ~emails_df["message_content"].str.contains(rule_value)
                    elif rule_predicate == "equals":
                        if rule_key == "from":
                            sender_email_query = emails_df["sender_email"] == rule_value
                        elif rule_key == "subject":
                            subject_query = emails_df["subject"] == rule_value
                        else:
                            message_query = emails_df["message_content"] == rule_value
                    else:
                        if rule_key == "from":
                            sender_email_query = ~emails_df["sender_email"] == rule_value
                        elif rule_key == "subject":
                            subject_query = ~emails_df["subject"] == rule_value
                        else:
                            message_query = ~emails_df["message_content"] == rule_value

            # get the required results based on all/any
            if global_predicate == "all":
                email_results = emails_df[sender_email_query & subject_query & message_query & date_query]
            else:
                email_results = emails_df[sender_email_query | subject_query | message_query | date_query]

            # capture the message ids
            filtered_message_ids = email_results['message_id'].tolist()

            # instantiate gmail service
            service = build('gmail', 'v1', credentials=gmail_creds)

            # all possible labels for emails
            all_label_ids = ["INBOX", "SPAM", "TRASH", "UNREAD"]

            # list of label_ids to associated with the filtered messages
            add_label_ids = []

            # capture the action from the rule and add it to add_label_ids, remove it from all_label_ids
            # the filtered messages will be associated with all_label_ids and will be disassociated from the
            # rest of the label_ids represented by all_label_ids
            move_label_id = rules[rule_name]["actions"]["move_message_to"].upper()
            add_label_ids.append(move_label_id)
            all_label_ids.remove(move_label_id)

            read_label_id = rules[rule_name]["actions"]["mark_message_as"].upper()
            # if the message needs to marked as unread, add it to add_label_ids and remove it from all_label_ids
            if read_label_id == "UNREAD":
                all_label_ids.remove(read_label_id)
                add_label_ids.append(read_label_id)
            request_body = {'ids': filtered_message_ids, 'addLabelIds': add_label_ids, \
                            'removeLabelIds': all_label_ids}
            # call the google gmail batchModify API
            service.users().messages().batchModify(userId='me', body=request_body).execute()