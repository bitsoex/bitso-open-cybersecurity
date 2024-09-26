#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
import os.path
from os import path
import sys
import requests
import json
from requests.structures import CaseInsensitiveDict
import time

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

# Function to send slack notifications
def send_slack_notification(message):
    payload = {'text': message, "username": "Daily Vulnerability Summary" }
    headers = {'Content-Type': 'application/json'}  
    requests.post(slack_webhook, json=payload, headers=headers)

slack_webhook = get_secret("bitso/open_pocketsoc/slack_channel_rss_int")
pwn_key = get_secret("bitso/open_pocketsoc/haveibeenpwned_api_key")
pwn_accounts = ["email1@domain.com", "email2@domain.com"]

#Create or open existing database
def check_db():
    if path.exists('pwn.db'):
        connection = sqlite3.connect("pwn.db", isolation_level=None)
    else:
        connection = sqlite3.connect("pwn.db", isolation_level=None)
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE breaches (account TEXT, leak TEXT, first_seen DATETIME)")
        cursor.close()
    return connection

#Reset DB
def truncate():
    connection = check_db()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM breaches")
    cursor.close()
  

#Scan for new pulses
def scan():
    active_breaches = 0
    connection = check_db()
    for email in pwn_accounts:
        headers = {'hibp-api-key': pwn_key}
        response = requests.get("https://haveibeenpwned.com/api/v3/breachedaccount/" + str(email), headers=headers)
        if response.status_code == 200:
            output = json.loads(response.content)
            for i in output:
                #Add transaction
                cursor = connection.cursor()
                #Check if entry exists
                cursor.execute("SELECT COUNT(*) AS CNT FROM breaches WHERE account = ? AND leak = ? LIMIT 1", (email, i['Name']))
                row = cursor.fetchone()[0]
                if str(row) != "1":
                    active_breaches += 1
                    cursor.execute("INSERT INTO breaches (account, leak, first_seen) values (?, ?, CURRENT_TIMESTAMP)", (email, i['Name']))
                cursor.close()
        time.sleep(2)
    if active_breaches > 0:
        message = f"pwnmon", str(active_breaches) +" new email breaches found."
        send_slack_notification(message)

def main(event, lambda_context):
    truncate()
    scan()