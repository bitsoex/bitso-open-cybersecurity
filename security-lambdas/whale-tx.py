import requests
import json
import boto3
from botocore.exceptions import ClientError


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
slack_webhook_url = get_secret("bitso/open_pocketsoc/slack_channel_rss_int-ownername")

aKey = get_secret("bitso/open_pocketsoc/whale-tx-ownername")

api_url = f"https://api.whale-alert.io/v1/transactions?api_key={aKey}"

# Define los parámetros para la solicitud
params = {
    "blockchain": "ethereum,bitcoin,tron",  # Lista de blockchains
    "min_value": 100000  # Valor mínimo en USD
}

# Función para enviar mensaje a Slack
def send_to_slack(message):
    try:
        payload = {"text": message}
        response = requests.post(slack_webhook_url, json=payload)
        if response.status_code != 200:
            print(f"Error sending message to Slack: {response.status_code}, {response.text}")
        else:
            print("Message sent to Slack successfully.")
    except Exception as e:
        print(f"Error occurred while sending message to Slack: {e}")

# Función para procesar y formatear la alerta
def parse_alert(data):
    blockchain = data.get("blockchain", "N/A")
    transaction_type = data.get("transaction_type", "N/A")
    from_wallet = data.get("from", "N/A")
    to_wallet = data.get("to", "N/A")
    amounts = data.get("amounts", [])
    amount_info = ""
    if amounts:
        amount = amounts[0].get("amount", "N/A")
        symbol = amounts[0].get("symbol", "N/A")
        amount_info = f"{amount} {symbol}"

    text = data.get("text", "N/A")
    transaction_hash = data.get("hash", "N/A")
    fee = data.get("fee", "N/A")
    fee_symbol = data.get("fee_symbol", "N/A")
    fee_symbol_price = data.get("fee_symbol_price", "N/A")

    formatted_message = (
        f"Blockchain: {blockchain}\n"
        f"Transaction Type: {transaction_type}\n"
        f"From: {from_wallet}\n"
        f"To: {to_wallet}\n"
        f"Amounts: {amount_info}\n"
        f"Text: {text}\n"
        f"Hash: {transaction_hash}\n"
        f"Fee: {fee} {fee_symbol}\n"
        f"Fee Symbol Price: {fee_symbol_price} USD"
    )

    return formatted_message

# Función para obtener transacciones desde la API REST
def get_transactions():
    try:
        response = requests.get(api_url, params=params)
        if response.status_code != 200:
            print(f"Error fetching data from Whale Alert API: {response.status_code}, {response.text}")
            return

        # Procesar las transacciones
        transactions = response.json().get('transactions', [])
        for transaction in transactions:
            alert_message = parse_alert(transaction)
            print(alert_message)

            # Enviar alerta a Slack
            send_to_slack(alert_message)

    except Exception as e:
        print(f"Error occurred while fetching transactions: {e}")

# Función principal para ejecutar la lógica
def main(event=None, lambda_context=None):
    get_transactions()
    print("Process finished. Results sent via Slack.")

if __name__ == "__main__":
    main()