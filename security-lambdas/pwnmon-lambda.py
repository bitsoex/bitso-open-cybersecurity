import requests
import json
import boto3

# Function to get secret value from AWS Secrets Manager
def get_secret(secret_name):
    region_name = "us-east-2"
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e
    secret = get_secret_value_response['SecretString']
    return secret


#Getting keys and secrets, emails to verify and API Endpoint
HIBP_API_KEY = get_secret("bitso/open_pocketsoc/haveibeenpwned_api_key-ownername")
SLACK_WEBHOOK_URL = get_secret("bitso/open_pocketsoc/slack_channel_rss_int-ownername")
EMAILS_TO_CHECK = ["email1@example.com", "email2@example.com"]  # List of emails to check
HIBP_API_URL = "https://haveibeenpwned.com/api/v3/breachedaccount/"

# Function to send message to Slack
def send_to_slack(message):
    slack_data = {"text": message}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(SLACK_WEBHOOK_URL, data=json.dumps(slack_data), headers=headers)
    
    if response.status_code == 200:
        print("Notification sent successfully.")
    else:
        print(f"Failed to send notification. Status code: {response.status_code}, response: {response.text}")

# Function to check if an email is pwned
def check_email(email):
    headers = {
        'hibp-api-key': HIBP_API_KEY,
        'User-Agent': 'Pwned-Email-Checker'
    }
    response = requests.get(HIBP_API_URL + email, headers=headers, params={'truncateResponse': 'false'})

    if response.status_code == 200:
        breaches = response.json()
        return breaches
    elif response.status_code == 404:
        # 404 means no breach found for the email
        return None
    else:
        # For other status codes, print an error message
        print(f"Error checking email {email}: {response.status_code}")
        return None

# Function to process the email list
def check_emails_and_notify():
    for email in EMAILS_TO_CHECK:
        print(f"Checking email: {email}")
        breaches = check_email(email)
        
        if breaches:
            # If breaches found, construct the message
            message = f"*Email:* {email} has been found in the following breaches:\n"
            for breach in breaches:
                message += f"- {breach['Name']} (Date: {breach['BreachDate']})\n"
            send_to_slack(message)
        else:
            print(f"No breach found for email: {email}")

# Main function
def main(event, lambda_context):
    check_emails_and_notify()