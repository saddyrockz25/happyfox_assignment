from authenticate import authenticate
from fetch_emails import fetch_emails
from modify_emails import modify_emails
from add_email_rules import add_email_rules



if __name__ == '__main__':
    gmail_creds = authenticate()
    if gmail_creds:
        fetch_emails(gmail_creds)
        add_email_rules()
        modify_emails(gmail_creds)