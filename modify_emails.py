from googleapiclient.discovery import build

import json, math
from datetime import datetime
from sqlalchemy import create_engine

import pandas as pd

db_config_file = open('config.json')
db_config = json.load(db_config_file)


# Function to determine the labels that need to be added/removed to the filtered messages
def prepare_labels_for_filtering_emails(move_message_label_id, message_read_label_id):

    # all possible labels for emails
    all_label_ids = ["INBOX", "SPAM", "TRASH", "UNREAD"]

    # list of label_ids to associated with the filtered messages
    add_label_ids = []

    # initialize labels to be removed with all label ids
    remove_label_ids = all_label_ids.copy()

    # capture the action from the rule and add it to add_label_ids, remove it from remove_label_ids
    # the filtered messages will be associated with add_label_ids and will be disassociated from the
    # rest of the label_ids represented by remove_label_ids
    add_label_ids.append(move_message_label_id)
    remove_label_ids.remove(move_message_label_id)

    # if the message needs to marked as unread, add it to add_label_ids and remove it from remove_label_ids
    if message_read_label_id == "UNREAD":
        remove_label_ids.remove(message_read_label_id)
        add_label_ids.append(message_read_label_id)

    return add_label_ids, remove_label_ids

# Function to combine results of all filters for a rule depending on global predicate(all/any)
def combine_all_filters(emails_df, query_results, global_predicate):

    if global_predicate == "all":
        final_result = pd.Series([True] * len(emails_df))
        for each_query_result in query_results:
            final_result = final_result & each_query_result
    else:
        final_result = pd.Series([False] * len(emails_df))
        for each_query_result in query_results:
            final_result = final_result | each_query_result

    return emails_df[final_result]

# Function to process rules that involve any string field
def process_string_field_filter(emails_df, rule_key, rule_value, rule_predicate):
    # map of key specified in the json rule to the column name in the database
    rule_key_attribute_map = {
        "from": "sender_email",
        "subject": "subject",
        "date_received": "date",
        "message": "message_content"
    }

    if rule_predicate == "contains":
        return (emails_df[rule_key_attribute_map[rule_key]].str.contains(rule_value))
    elif rule_predicate == "does_not_contain":
        return (~emails_df[rule_key_attribute_map[rule_key]].str.contains(rule_value))
    elif rule_predicate == "equals":
        return (emails_df[rule_key_attribute_map[rule_key]] == rule_value)
    else:
        return (~emails_df[rule_key_attribute_map[rule_key]] == rule_value)


# Function to process rules that involve the date received field
def process_date_field_filter(emails_df, rule_time_value, rule_time_unit, rule_predicate):

    time_unit_map = {
        "days": 1,
        "months": 30
    }

    # compute the requisite start and end dates
    today = datetime.now()
    end_date = str(today.date())
    start_date = str(datetime.fromtimestamp(math.floor(today.timestamp()) - \
                                            (int(rule_time_value) * time_unit_map[rule_time_unit] * 86400)).date())

    # build the query depending on the predicate
    if rule_predicate == "less_than":
        return (emails_df["date"].dt.strftime("%Y-%m-%d %H:%M:%S") > start_date) & \
                             (emails_df["date"].dt.strftime("%Y-%m-%d %H:%M:%S") < end_date)
    else:
        return (emails_df["date"].dt.strftime("%Y-%m-%d %H:%M:%S") < start_date)

# Function to modify emails in gmail based on rules in the json file
def modify_emails(gmail_creds):
    email_rules_file = open('email_rules.json')
    rules = json.load(email_rules_file)


    # instantiate postgres connection
    postgres_engine = create_engine("postgresql://" + db_config["db_username"] + ":" + \
    db_config["db_password"] + "@" + db_config["db_server"] + ":" + \
    db_config["db_port"] + "/" + db_config["db_name"])

    with postgres_engine.connect() as connection:

        # read all data initially using pandas
        # pandas is used for better filtering capabilities
        emails_df = pd.read_sql("select * from emails", connection)

        for rule_name in rules:

            # Store the series of boolean array, that results from each query/filter in the rule
            query_results = []

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

                    query_results.append(process_date_field_filter\
                                             (emails_df, rule_time_value, rule_time_unit, rule_predicate))
                else:
                    # similarly build queries for sender_email, subject and message content depending on predicate
                    query_results.append(process_string_field_filter\
                                             (emails_df, rule_key, rule_value, rule_predicate))

            # get the required results based on all/any
            email_results = combine_all_filters(emails_df, query_results, global_predicate)

            # capture the message ids
            filtered_message_ids = email_results['message_id'].tolist()

            # instantiate gmail service
            service = build('gmail', 'v1', credentials=gmail_creds)

            # capture the actions that needs to be performed with the filtered messages
            move_message_label_id = rules[rule_name]["actions"]["move_message_to"].upper()
            message_read_label_id = rules[rule_name]["actions"]["mark_message_as"].upper()

            # determine the labels to be added/removed to filtered messages based on the actions specified
            add_label_ids, remove_label_ids = prepare_labels_for_filtering_emails\
                (move_message_label_id, message_read_label_id)
            request_body = {'ids': filtered_message_ids, 'addLabelIds': add_label_ids, \
                            'removeLabelIds': remove_label_ids}

            # call the google gmail batchModify API to add/remove determined labels on Gmail
            service.users().messages().batchModify(userId='me', body=request_body).execute()