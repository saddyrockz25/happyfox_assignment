import json
import tkinter as tk


def create_dropdown(root, options, default, rules_objects_list):
    dropdown_value = tk.StringVar()
    dropdown_value.set(default)
    drop_down = tk.OptionMenu(root, dropdown_value, *options)
    rules_objects_list.append(dropdown_value)
    return drop_down

# Function to add filter rules for emails
# Emails can be filtered based on sender email, subject, message body and received date
def add_email_rules():
    # Create root window object
    root = tk.Tk()

    # Adjust size
    root.geometry("800x800")

    # Variable that keeps track of the number of lines in the window
    lineCount = 0

    # Variable that holds the list of all objects in the window
    rules_objects_list = []

    rules_json = {}

    # Function to dynamically add objects on the window so as to create new filter rules
    def add():
        nonlocal lineCount
        nonlocal rules_objects_list

        rule_predicate_options = [
            "all",
            "any"
        ]
        conditions = [
            "from",
            "subject",
            "message"
            "date_received",
        ]

        string_predicate_options = [
            "contains",
            "does_not_contain",
            "equals",
            "not_equals"
        ]

        date_predicate_options = [
            "less_than",
            "greater_than"
        ]

        date_options = [
            "days",
            "months"
        ]

        message_label_options = [
            "inbox",
            "spam",
            "trash"
        ]

        message_read_options = [
            "read",
            "unread"
        ]

        # Object used to give a name to the rule
        rule_label = tk.Label(root, text='Rule Name')
        rule_name = tk.StringVar()
        rule_name_element = tk.Entry(root, textvariable=rule_name, font=('calibre', 10, 'normal'))
        rules_objects_list.append(rule_name)

        # Dropdown Object to select a predicate for the rule - all/any
        rule_predicate = tk.Label(root, text='Rule Predicate')
        rule_drop_down = create_dropdown(root, rule_predicate_options, "all", rules_objects_list)

        # Dropdown object to select key on which the filter needs to be applied
        # Pre-selected as "from"
        from_drop_down = create_dropdown(root, conditions, "from", rules_objects_list)

        # Dropdown object to select type of predicate on the selected key
        # Pre-selected as "contains"
        from_predicate_drop_down = create_dropdown(root, string_predicate_options, "contains", rules_objects_list)

        # Object to capture the value to be used to filter on the selected key
        from_email = tk.StringVar()
        from_email_element = tk.Entry(root, textvariable=from_email, font=('calibre', 10, 'normal'))
        rules_objects_list.append(from_email)

        # Dropdown object to select key on which the filter needs to be applied
        # Pre-selected as "subject", signifying subject of the mail
        subject_drop_down = create_dropdown(root, conditions, "subject", rules_objects_list)

        # Dropdown object to select type of predicate on subject
        # Pre-selected as "contains"
        subject_predicate_drop_down = create_dropdown(root, string_predicate_options, "contains", rules_objects_list)

        # Object to capture the value to be used to filter on the subject
        subject = tk.StringVar()
        subject_element = tk.Entry(root, textvariable=subject, font=('calibre', 10, 'normal'))
        rules_objects_list.append(subject)

        # Similarly for message and date received objects
        message_drop_down = create_dropdown(root, conditions, "message", rules_objects_list)
        message_predicate_drop_down = create_dropdown(root, string_predicate_options, "contains", rules_objects_list)

        message = tk.StringVar()
        message_element = tk.Entry(root, textvariable=message, font=('calibre', 10, 'normal'))
        rules_objects_list.append(message)

        date_received_dropdown = create_dropdown(root, conditions, "date_received", rules_objects_list)
        date_predicate_drop_down = create_dropdown(root, date_predicate_options, "less_than", rules_objects_list)

        date_received = tk.StringVar()
        date_received_element = tk.Entry(root, textvariable=date_received, font=('calibre', 10, 'normal'))
        rules_objects_list.append(date_received)

        date_options_drop_down = create_dropdown(root, date_options, "days", rules_objects_list)

        # Actions that needs to be carried out for the rule
        rule_action_label = tk.Label(root, text='Rule Actions')

        # Dropdown object to select the label of the message - INBOX, SPAM, TRASH etc.
        # Pre-selected as "inbox"
        move_message_label = tk.Label(root, text='Move message to')
        move_message_drop_down = create_dropdown(root, message_label_options, "inbox", rules_objects_list)

        # Dropdown object to select the read status of the message - READ, UNREAD
        mark_message_label = tk.Label(root, text='Mark message as')
        mark_message_drop_down = create_dropdown(root, message_read_options, "unread", rules_objects_list)

        # Populate the window in the form of a grid
        rule_label.grid(row=lineCount, column=0)
        rule_name_element.grid(row=lineCount, column=1)
        rule_predicate.grid(row=lineCount + 1, column=0)
        rule_drop_down.grid(row=lineCount + 1, column=1)

        from_drop_down.grid(row=lineCount + 2, column=0)
        from_predicate_drop_down.grid(row=lineCount + 2, column=1)
        from_email_element.grid(row=lineCount + 2, column=2)

        subject_drop_down.grid(row=lineCount + 3, column=0)
        subject_predicate_drop_down.grid(row=lineCount + 3, column=1)
        subject_element.grid(row=lineCount + 3, column=2)

        message_drop_down.grid(row=lineCount + 4, column=0)
        message_predicate_drop_down.grid(row=lineCount + 4, column=1)
        message_element.grid(row=lineCount + 4, column=2)

        date_received_dropdown.grid(row=lineCount + 5, column=0)
        date_predicate_drop_down.grid(row=lineCount + 5, column=1)
        date_received_element.grid(row=lineCount + 5, column=2)
        date_options_drop_down.grid(row=lineCount + 5, column=3)

        rule_action_label.grid(row=lineCount + 6, column=0)
        move_message_label.grid(row=lineCount + 7, column=0)
        move_message_drop_down.grid(row=lineCount + 7, column=1)
        mark_message_label.grid(row=lineCount + 8, column=0)
        mark_message_drop_down.grid(row=lineCount + 8, column=1)


        add_btn.grid(row=lineCount + 9, column = 0)
        sub_btn.grid(row=lineCount + 10, column= 0)

        lineCount += 12
        pass

    def submit():
        nonlocal rules_json

        # Each rule has 17 elements, hence it is hardcoded as 17
        no_of_rules = len(rules_objects_list) // 17

        for iteration in range(no_of_rules):

            rule_name_object = rules_objects_list.pop(0)
            rule_name = rule_name_object.get()
            rules_json[rule_name] = {}

            rule_predicate_object = rules_objects_list.pop(0)
            rule_predicate = rule_predicate_object.get()
            rules_json[rule_name][rule_predicate] = {}

            # The iteration is hardcoded as 4 since each rule consists of 4 keys - from, subject, message and date
            # It is fixed as 4 for assignment purpose
            individual_rules = []
            for i in range(4):
                individual_rule_dict = {}
                individual_rule_object = rules_objects_list.pop(0)
                individual_rule = individual_rule_object.get()
                individual_rule_dict["field"] = individual_rule
                individual_rule_predicate_object = rules_objects_list.pop(0)
                individual_rule_predicate = individual_rule_predicate_object.get()
                individual_rule_dict["predicate"] = individual_rule_predicate
                individual_rule_value_object = rules_objects_list.pop(0)
                individual_rule_value = individual_rule_value_object.get()
                individual_rule_option = ''
                if i and not (i % 3):
                    individual_rule_option_object = rules_objects_list.pop(0)
                    individual_rule_option = ' ' + individual_rule_option_object.get()
                individual_rule_dict["value"] = individual_rule_value + individual_rule_option
                individual_rules.append(individual_rule_dict)

            rules_json[rule_name][rule_predicate] = individual_rules

            move_message_object = rules_objects_list.pop(0)
            move_message_label = move_message_object.get()
            message_read_object = rules_objects_list.pop(0)
            message_read_option = message_read_object.get()
            rules_json[rule_name]["actions"] = {
                "move_message_to":move_message_label,
                "mark_message_as":message_read_option
            }

        with open("email_rules.json", "w") as outfile:
            outfile.write(json.dumps(rules_json, indent=4))

        # Close the window
        root.quit()

    # The window initially only has an add and a submit button
    add_btn = tk.Button(root, text='+', command=add)
    sub_btn = tk.Button(root, text='Submit', command=submit)
    add_btn.grid(row=0,column=1)
    sub_btn.grid(row=1, column=1)

    # Display the window
    root.mainloop()