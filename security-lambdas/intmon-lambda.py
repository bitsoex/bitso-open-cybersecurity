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
slack_channel_rss_int = get_secret("bitso/open_pocketsoc/slack_channel_rss_int-ownername")
intel_otx_key = get_secret("bitso/open_pocketsoc/intel_otx_key-ownername")

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
            output += str(i['name']) + ": " + str(i['description']) + "\n\n"
    if output != "":
        send(output)

#Run
def main(event, lambda_context):
    get_intel()
    print("\t[*] Process finished. Results sent via Slack.")