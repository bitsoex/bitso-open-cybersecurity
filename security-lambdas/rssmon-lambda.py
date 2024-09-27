import logging
import boto3
from botocore.exceptions import ClientError
import feedparser
import requests

# Configurar el registro para el seguimiento de errores y mensajes
logging.basicConfig(level=logging.INFO)

# Specific keywords and phrases to monitor in the RSS feeds
RSS_KEYWORDS = [
    "bitso", "aws", "amazon", "okta", "twilio", "slack",
    "crowdstrike", "terraform", "chrome", "macos",
    "windows", "jira", "cloudflare", "confluence", "splunk",
    "datadog", "endpointcentral", "manageengine", "github", "zoom", "mozilla", "kubernetes",
]

# List of RSS feeds to monitor with keyword filters
RSS_FEEDS = [
    "https://feeds.feedburner.com/TheHackersNews",
    "https://www.darkreading.com/rss.xml",
    "https://cybersecurity.att.com/site/blog-all-rss",
    "http://feeds.trendmicro.com/TrendMicroResearch",
    "https://www.cisa.gov/uscert/ncas/alerts.xml",
    "https://www.cisecurity.org/feed/advisories",
    "https://www.mandiant.com/resources/rss.xml/all",
    "https://blog.talosintelligence.com/feeds/posts/default/-/Headlines",
    "https://blog.talosintelligence.com/feeds/posts/default/-/Threat%20Roundup",
    "https://blog.talosintelligence.com/feeds/posts/default/-/threats",
    "https://cyware.com/allnews/feed",
    "https://www.infosecurity-magazine.com/rss/news/",
    "https://www.immunebytes.com/blog/feed/",
    "https://www.bleepingcomputer.com/feed/",
    "https://cloudblog.withgoogle.com/topics/threat-intelligence/rss/",
    "https://www.elastic.co/security-labs/rss/feed.xml"
]

# List of RSS feeds to monitor without keyword filters (bypass filters)
RSS_FEEDS_BYPASS = [
    "https://web3isgoinggreat.com/feed.xml",
    "https://newsletter.blockthreat.io/feed"
]

# Function to get secret value from AWS Secrets Manager
def get_secret(secret_name):
    region_name = "us-east-2"
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)
    
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = get_secret_value_response['SecretString']
        return secret
    except ClientError as e:
        logging.error(f"Error retrieving secret {secret_name}: {e}")
        raise

# Get Slack webhook URL from Secrets Manager
slack_channel_rss_int = get_secret("bitso/open_pocketsoc/slack_channel_rss_int-ownername")

# Function to send notification to Slack
def send_to_slack(message):
    try:
        headers = {"Content-type": "application/json"}
        data = {"text": f"[RSSMon]\n{message}"}
        response = requests.post(slack_channel_rss_int, headers=headers, json=data)
        
        if response.status_code != 200:
            logging.error(f"Error sending message to Slack: {response.status_code}, {response.text}")
        else:
            logging.info("Message sent to Slack successfully.")
    except Exception as e:
        logging.error(f"Error occurred while sending message to Slack: {e}")

# Function to check if an entry matches the keywords
def matches_keywords(entry):
    title = entry.get('title', '').lower()
    description = entry.get('description', '').lower()
    return any(keyword in title or keyword in description for keyword in RSS_KEYWORDS)

# Function to fetch and process RSS feeds
def get_feeds():
    output = ""
    news_found = 0

    # Process feeds with keyword filters
    for feed_url in RSS_FEEDS:
        try:
            d = feedparser.parse(feed_url)
            source = d.get('feed', {}).get('title', 'RSSMon')
            logging.info(f"Querying {source}...")
            
            for entry in d['entries']:
                if matches_keywords(entry):
                    title = entry.get('title', '')
                    link = entry.get('link', '')
                    if title:
                        news_found += 1
                        output += f"<{link}|{title}>\n\n"
        except Exception as e:
            logging.error(f"Error processing feed {feed_url}: {e}")

    # Process feeds bypassing filters
    for feed_url in RSS_FEEDS_BYPASS:
        try:
            d = feedparser.parse(feed_url)
            source = d.get('feed', {}).get('title', 'RSSMon')
            logging.info(f"Querying {source} (with filter bypass)...")
            
            for entry in d['entries']:
                title = entry.get('title', '')
                link = entry.get('link', '')
                if title:
                    news_found += 1
                    output += f"<{link}|{title}>\n\n"
        except Exception as e:
            logging.error(f"Error processing feed {feed_url}: {e}")
    
    # Send Slack notification if new news found
    if news_found > 0:
        send_to_slack(output)

# Main function to run the script
def main(event, lambda_context):
    get_feeds()
    logging.info("Process finished. Results sent via Slack.")

if __name__ == "__main__":
    main({}, {})