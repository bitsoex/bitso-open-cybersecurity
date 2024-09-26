#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import sqlite3
import os.path
from os import path
import sys
import requests
import json
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Configuration & notifier
import settings

# Get Slack webhook URL from Secrets Manager
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

# Slack webhook for notifications
slack_webhook_url = get_secret("bitso/open_pocketsoc/whale-tx")

# Send a message to Slack
def send_to_slack(message):
    try:
        url = slack_webhook_url
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({"text": message})
        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 200:
            print(f"Error sending message to Slack. Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Exception occurred while sending message to Slack: {e}")

# Create or open existing database
def check_db():
    if path.exists('trx.db'):
        connection = sqlite3.connect("trx.db", isolation_level=None)
    else:
        connection = sqlite3.connect("trx.db", isolation_level=None)
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE trans (
                ophash TEXT, 
                direction TEXT, 
                currency TEXT, 
                blockchain TEXT, 
                crypto_amount TEXT, 
                usd_amount TEXT, 
                from_addr TEXT, 
                to_addr TEXT, 
                exchange TEXT, 
                first_seen DATETIME
            )
        """)
        cursor.close()
    return connection

# Reset DB
def truncate():
    connection = check_db()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM trans")
    cursor.close()
    send_to_slack("DB initialization completed.")
    print("Database truncated.")

# Scan - Scan all transactions
def scan():
    output = ""
    connection = check_db()
    url = f"https://api.whale-alert.io/v1/transactions?api_key={settings.trans_api_key}"
    json_out = requests.get(url).json()
    transactions = json_out['transactions']
    trans_count = 0
    for transact in transactions:
        trans_direction = ""
        trans_block = transact['blockchain']
        trans_sym = transact['symbol']
        trans_hash = str(transact['hash'])
        trans_from_addr = transact['from']['address']
        trans_to_addr = transact['to']['address']
        trans_amount = str(transact['amount'])
        trans_amount_usd = str(transact['amount_usd'])
        trans_date_unix = int(transact['timestamp'])
        trans_date = datetime.utcfromtimestamp(trans_date_unix).strftime('%Y-%m-%d %H:%M:%S')
        trans_exchange = ""
        trans_from = ""
        trans_to = ""
        this_transact = ""

        try:
            trans_from = transact['from']['owner']
            if trans_from in settings.trans_subjectFilter:
                trans_direction = "outgoing"
                this_transact = f"[Outgoing] From {trans_from_addr} to {trans_to_addr}. ${trans_sym} {trans_amount} (USD {trans_amount_usd}).\n"
        except Exception as e:
            pass
        try:
            trans_to = transact['to']['owner']
            if trans_to in settings.trans_subjectFilter:
                trans_direction = "incoming"
                this_transact = f"[Incoming] From {trans_from_addr} to {trans_to_addr}. ${trans_sym} {trans_amount} (USD {trans_amount_usd}).\n"
        except Exception as e:
            pass

        if trans_from in settings.trans_subjectFilter or trans_to in settings.trans_subjectFilter:
            trans_exchange = trans_to if trans_from in settings.trans_subjectFilter else trans_from
            if trans_exchange == "":
                trans_exchange = "Unknown"

            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) AS CNT FROM trans WHERE ophash = ? LIMIT 1", ([trans_hash]))
            row = cursor.fetchone()[0]

            if str(row) != "1":
                output += this_transact
                trans_count += 1
                cursor.execute("""
                    INSERT INTO trans 
                    (ophash, direction, currency, blockchain, crypto_amount, usd_amount, from_addr, to_addr, exchange, first_seen) 
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (str(trans_hash), str(trans_direction), str(trans_sym), str(trans_block), str(trans_amount), str(trans_amount_usd), str(trans_from_addr), str(trans_to_addr), str(trans_exchange), trans_date))
            cursor.close()

    if output:
        send_to_slack(output.replace('"', ''))
        print(f"{trans_count} outstanding transactions registered.")

# Main function to run in Lambda
def main(event=None, lambda_context=None):
    if len(sys.argv) <= 1:
        print("Invalid arguments.")
    elif str(sys.argv[1]) == "truncate":
        truncate()
    elif str(sys.argv[1]) == "scan":
        scan()

if __name__ == "__main__":
    main({}, {})
