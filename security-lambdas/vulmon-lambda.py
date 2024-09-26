#!/usr/bin/python3
# -*- coding: utf-8 -*-
#Script to fetch intelligence pulses from OTX.
import logging
import boto3
from botocore.exceptions import ClientError
import os.path
from os import path
import sys
import sqlite3
import feedparser
import requests
from requests.structures import CaseInsensitiveDict

#Set: Feeds
#Products to monitor (lowercase)
vuln_keywords = ["aws", "java", "amazon", "splunk", "php", "windows", "desktop central", "twilio"]
#Feeds to monitor
vuln_feeds = ["https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss-analyzed.xml"]

#Get: DB
def check_db():
    try:
        s3 = boto3.resource('s3')
        s3.Bucket("pocketsoc-files").download_file("vul.db", "/tmp/vul.db")
    except:
        print("[!] DB Not found. Creating it.")
    if path.exists('/tmp/vul.db'):
        connection = sqlite3.connect("/tmp/vul.db", isolation_level=None)
    else:
        connection = sqlite3.connect("/tmp/vul.db", isolation_level=None)
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE vulns (title TEXT, description TEXT, link TEXT, source TEXT, first_seen DATETIME)")
        cursor.close()
    return connection

#Put: DB
def update_db():
    try:
        s3 = boto3.client('s3')
        with open("/tmp/vul.db", "rb") as f:
            s3.upload_fileobj(f, "pocketsoc-files", "vul.db")
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
slack_channel_vulns = get_secret("bitso/open_pocketsoc/slack_channel_vulns")

#Post: Slack notification
def send(message):
    try:
        url = slack_channel_vulns
        headers = CaseInsensitiveDict()
        headers["Content-type"] = "application/json"
        data = '{"text":"[VULMon]\n'+ str(message) +'"}'
        resp = requests.post(url, headers=headers, data=str(data).encode('utf-8'))
    except Exception as e:
        print(e)

#Get: Vuln feed
def get_vulns():
    output = ""
    vulns_found = 0
    connection = check_db()
    for i in vuln_feeds:
        d = feedparser.parse(i)
        source = ""
        try:
            source = d['feed']['title']
        except:
            source = "VULMon"
        print("[*] Querying " + source + "...")
        for entry in d['entries']:
            if any(ext in entry['title'].lower() for ext in vuln_keywords) or any(ext in entry['description'].lower() for ext in vuln_keywords):
                title = ""
                description = ""
                link = ""
                try:
                    title = entry['title']
                except:
                    title = ""
                try:
                    description = entry['description']
                except:
                    description = ""
                try:
                    link = entry['link']
                except:
                    link = ""
                if title != "":
                    #Add transaction
                    cursor = connection.cursor()
                    #Check if entry exists
                    cursor.execute("SELECT COUNT(*) AS CNT FROM vulns WHERE title = ? LIMIT 1", ([entry['title']]))
                    row = cursor.fetchone()[0]
                    if str(row) != "1":
                        vulns_found += 1
                        cursor.execute("INSERT INTO vulns (title, description, link, source, first_seen) values (?, ?, ?, ?, CURRENT_TIMESTAMP)", (title, description, link, source))
                        output += "<" + str(entry['link']) + "|" + str(entry['title']) + ">\n"+ str(description)+"\n\n--"
                    cursor.close()
    if output != "":
        update_db()
        send(output)

#Run
def main(event, lambda_context):
    get_vulns()
    print("\t[*] Process finished. Results sent via Slack.")