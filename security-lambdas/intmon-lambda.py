#!/usr/bin/python3
# -*- coding: utf-8 -*-
#Script to fetch intelligence pulses from OTX.
import logging
import boto3
from botocore.exceptions import ClientError
import time
import os
import os.path
from os import path
import requests
import json
import sqlite3
from requests.structures import CaseInsensitiveDict
from datetime import date

#Set: Feeds
#Keywords to monitor (lowercase)
intel_keywords = ["crypto", "cryptocurrency", "bitso", "aws", "amazon", "okta", "nft", "twilio"]

#Get: DB
def check_db():
    try:
        s3 = boto3.resource('s3')
        s3.Bucket("open-pocketsoc-files").download_file("int.db", "/tmp/int.db")
    except:
        print("[!] DB Not found. Creating it.")
    if path.exists('/tmp/int.db'):
        connection = sqlite3.connect("/tmp/int.db", isolation_level=None)
    else:
        connection = sqlite3.connect("/tmp/int.db", isolation_level=None)
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE intel (pulse_id TEXT, name TEXT, description TEXT, first_seen DATETIME)")
        cursor.close()
    return connection

#Put: DB
def update_db():
    try:
        s3 = boto3.client('s3')
        with open("/tmp/int.db", "rb") as f:
            s3.upload_fileobj(f, "open-pocketsoc-files", "int.db")
    except Exception as e:
        print("[!] Error updating database:"+ str(e) +".")

#Get: Secrets
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

#Set: Secrets
slack_channel_rss_int = get_secret("bitso/open_pocketsoc/slack_channel_rss_int")
intel_otx_key = get_secret("bitso/open_pocketsoc/intel_otx_key")

#Post: Slack notification
def send(message):
    try:
        url = slack_channel_rss_int
        headers = CaseInsensitiveDict()
        headers["Content-type"] = "application/json"
        data = '{"text":"[INTMon]\n'+ str(message) +'"}'
        resp = requests.post(url, headers=headers, data=str(data).encode('utf-8'))
    except Exception as e:
        print(e)

#Get: All Intel pulses
def get_intel():
    output = ""
    connection = check_db()
    #AlienVault OTX
    today = date.today()
    pulses_found = 0
    fixed_month = ""
    if today.month < 10:
        fixed_month = "0" + str(today.month)
    else:
        fixed_month = str(today.month)
    url = "https://otx.alienvault.com/api/v1/pulses/activity?modified_since="+ str(today.year) +"-"+ fixed_month +"-01"
    headers = CaseInsensitiveDict()
    headers["X-OTX-API-KEY"] = intel_otx_key
    json_out = requests.get(url, headers=headers).json()
    results = json_out['results']
    for i in results:
        print(i['name'])
        if any(ext in i['name'].lower() for ext in intel_keywords) or any(ext in i['description'].lower() for ext in intel_keywords):
            #Add transaction
            cursor = connection.cursor()
            #Check if entry exists
            cursor.execute("SELECT COUNT(*) AS CNT FROM intel WHERE pulse_id = ? LIMIT 1", ([i['id']]))
            row = cursor.fetchone()[0]
            if str(row) != "1":
                pulses_found += 1
                cursor.execute("INSERT INTO intel (pulse_id, name, description, first_seen) values (?, ?, ?, ?)", (i['id'], i['name'], i['description'], i['modified']))
                output += str(i['name']) + ": " + str(i['description']) + "\n\n"
            cursor.close()
    if output != "":
        update_db()
        send(output)

#Run
def main(event, lambda_context):
    get_intel()
    print("\t[*] Process finished. Results sent via Slack.")