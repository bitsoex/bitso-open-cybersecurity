import feedparser
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

# RSS feed URL from SANS ISC
rss_feed_url = "https://isc.sans.edu/rssfeed.xml"

# Slack webhook URL (replace with your actual webhook URL)
slack_webhook_url = get_secret("bitso/open_pocketsoc/slack_channel_rss_int-ownername")

# Function to send message to Slack
def send_to_slack(title, link, pub_date):
    slack_data = {
        "text": f"*Title:* {title}\n*Link:* {link}\n*Published Date:* {pub_date}"
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(slack_webhook_url, data=json.dumps(slack_data), headers=headers)
    
    if response.status_code == 200:
        print(f"Notification sent successfully for: {title}")
    else:
        print(f"Failed to send notification. Status code: {response.status_code}, response: {response.text}")

# Parse the RSS feed
def check_feed():
    feed = feedparser.parse(rss_feed_url)
    
    for entry in feed.entries:
        title = entry.title
        link = entry.link
        pub_date = entry.published
        
        # Send the extracted data to Slack
        send_to_slack(title, link, pub_date)

def main(event, lambda_context):
    check_feed()