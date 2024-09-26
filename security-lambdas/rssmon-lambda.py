#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
import boto3
from botocore.exceptions import ClientError
import time
import os
import os.path
from os import path
import feedparser
import requests
import sqlite3
from requests.structures import CaseInsensitiveDict

# Specific keywords and phrases to monitor in the RSS feeds
rss_keywords = [
    "bitso", "aws", "amazon", "okta", "twilio", "slack",
    "crowdstrike", "terraform", "chrome", "macos",
    "windows", "jira", "cloudflare", "confluence", "splunk",
    "datadog", "endpointcentral", "manageengine", "github", "zoom", "mozilla", "kubernetes",
    ]
# List of RSS feeds to monitor with keyword filters
rss_feeds = [
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
    "https://cloudblog.withgoogle.com/topics/threat-intelligence/rss/"
    "https://www.elastic.co/security-labs/rss/feed.xml"
]

# List of RSS feeds to monitor without keyword filters (bypass filters)
rss_feeds_bypass = [
    "https://web3isgoinggreat.com/feed.xml",
    "https://newsletter.blockthreat.io/feed"
]

# Function to check if the database exists and download it or create a new one if not
def check_db():
    try:
        s3 = boto3.resource('s3')
        s3.Bucket("pocketsoc-files").download_file("rss.db", "/tmp/rss.db")
    except:
        print("[!] DB Not found. Creating it.")
    
    if path.exists('/tmp/rss.db'):
        connection = sqlite3.connect("/tmp/rss.db", isolation_level=None)
    else:
        connection = sqlite3.connect("/tmp/rss.db", isolation_level=None)
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE news (title TEXT, link TEXT, source TEXT, first_seen DATETIME)")
        cursor.close()
    
    return connection

# Function to upload the database back to S3
def update_db():
    try:
        s3 = boto3.client('s3')
        with open("/tmp/rss.db", "rb") as f:
            s3.upload_fileobj(f, "pocketsoc-files", "rss.db")
    except Exception as e:
        print("[!] Error updating database:" + str(e) + ".")

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

# Get Slack webhook URL from Secrets Manager
slack_channel_rss_int = get_secret("bitso/open_pocketsoc/slack_channel_rss_int")

# Function to send notification to Slack
def send(message):
    try:
        url = slack_channel_rss_int
        headers = CaseInsensitiveDict()
        headers["Content-type"] = "application/json"
        data = '{"text":"[RSSMon]\n' + str(message) + '"}'
        requests.post(url, headers=headers, data=str(data).encode('utf-8'))
    except Exception as e:
        print(e)

# Function to check if an entry matches the keywords
def matches_keywords(entry):
    title = entry.get('title', '').lower()
    description = entry.get('description', '').lower()
    return any(ext in title or ext in description for ext in rss_keywords)

# Function to fetch and process RSS feeds
def get_feeds():
    output = ""
    news_found = 0
    connection = check_db()
    
    # Process feeds with keyword filters
    for i in rss_feeds:
        d = feedparser.parse(i)
        source = d.get('feed', {}).get('title', 'RSSMon')
        print("[*] Querying " + source + "...")
        for entry in d['entries']:
            if matches_keywords(entry):
                title = entry.get('title', '')
                link = entry.get('link', '')
                if title:
                    cursor = connection.cursor()
                    cursor.execute("SELECT COUNT(*) AS CNT FROM news WHERE title = ? LIMIT 1", ([title]))
                    row = cursor.fetchone()[0]
                    if str(row) != "1":
                        news_found += 1
                        cursor.execute("INSERT INTO news (title, link, source, first_seen) values (?, ?, ?, CURRENT_TIMESTAMP)", (title, link, source))
                        output += "<" + link + "|" + title + ">\n\n"
                    cursor.close()
    
    # Process feeds bypassing filters
    for i in rss_feeds_bypass:
        d = feedparser.parse(i)
        source = d.get('feed', {}).get('title', 'RSSMon')
        print("[*] Querying " + source + " (with filter bypass)...")
        for entry in d['entries']:
            title = entry.get('title', '')
            link = entry.get('link', '')
            if title:
                cursor = connection.cursor()
                cursor.execute("SELECT COUNT(*) AS CNT FROM news WHERE title = ? LIMIT 1", ([title]))
                row = cursor.fetchone()[0]
                if str(row) != "1":
                    news_found += 1
                    cursor.execute("INSERT INTO news (title, link, source, first_seen) values (?, ?, ?, CURRENT_TIMESTAMP)", (title, link, source))
                    output += "<" + link + "|" + title + ">\n\n"
                cursor.close()
    
    # Update database and send Slack notification if new news found
    if news_found > 0:
        update_db()
        send(output)

# Main function to run the script
def main(event, lambda_context):
    get_feeds()
    print("\t[*] Process finished. Results sent via Slack.")

if __name__ == "__main__":
    main({}, {})