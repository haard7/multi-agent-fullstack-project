from flask import Flask, request, jsonify, redirect, url_for
import psycopg2
import re
import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

app = Flask(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

DB_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT', 5432)  
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

def insert_into_table(order_id, image_url, table_name):
    query = f"INSERT INTO {table_name} (orderid, product_img) VALUES (%s, %s)"
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(query, (order_id, image_url))
    conn.commit()
    conn.close()

def parse_email_content(email_body):
    order_id = re.search(r"Order ID:\s*(\d+)", email_body)
    image_url = re.search(r"Image URL:\s*(https?://[^\s]+)", email_body)
    issue_type = None

    if "defective product" in email_body.lower():
        issue_type = "Product_defect"
    elif "damaged package" in email_body.lower():
        issue_type = "Package_damaged"
    elif "fraudulent transaction" in email_body.lower():
        issue_type = "Fraud_transaction"
    
    if order_id and image_url and issue_type:
        return {
            "order_id": int(order_id.group(1)),
            "image_url": image_url.group(1),
            "issue_type": issue_type
        }
    return None

def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('./token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('./credentials.json', SCOPES)
        creds = flow.run_local_server(port=5001)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    service = build('gmail', 'v1', credentials=creds)
    return service

def get_unread_emails(service):
    try:
        results = service.users().messages().list(userId='me', labelIds=['UNREAD']).execute()
        messages = results.get('messages', [])
        emails = []
        
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            msg_str = msg['snippet']
            emails.append(msg_str)
            
            service.users().messages().modify(userId='me', id=message['id'], body={'removeLabelIds': ['UNREAD']}).execute()
        return emails
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None
    
#@app.route('/emails', methods=['GET'])
def fetch_emails():
    service = authenticate_gmail()
    emails = get_unread_emails(service)
    
    if emails is None:
        return jsonify({"error": "Failed to retrieve emails"}), 500
    
    success_count = 0
    for email_body in emails:
        parsed_data = parse_email_content(email_body)
        print(parsed_data)
        if parsed_data:
            try:
                insert_into_table(
                    parsed_data["order_id"],
                    parsed_data["image_url"],
                    parsed_data["issue_type"]
                )
                success_count += 1
            except Exception as e:
                print(f"Error saving to database: {str(e)}")
                return jsonify({"error": str(e)}), 500
    return jsonify({"message": f"Processed {success_count} emails successfully"}), 200

if __name__ == '__main__':
    with app.app_context():
        fetch_emails()  
    app.run()