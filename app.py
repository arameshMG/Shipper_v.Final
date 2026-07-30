from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests
import os

load_dotenv()

greeting = os.getenv("JOKE_API_GREETING")

def get_graph_token():
    tenant_id = os.getenv("GRAPH_TENANT_ID")
    client_id = os.getenv("GRAPH_CLIENT_ID")
    client_secret = os.getenv("GRAPH_CLIENT_SECRET")

    with open("debug_log.txt", "w") as f:
        f.write(f"TENANT ID: {tenant_id}\n")
        f.write(f"CLIENT ID: {client_id}\n")
        f.write(f"CLIENT SECRET: {client_secret}\n")

    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }

    response = requests.post(url, data=data)

    with open("debug_log.txt", "a") as f:
        f.write(f"STATUS CODE: {response.status_code}\n")
        f.write(f"RAW RESPONSE: {response.text}\n")

    token_data = response.json()
    return token_data["access_token"]

def get_user_address(user_email, token):
    url = f"https://graph.microsoft.com/v1.0/users/{user_email}?$select=displayName,streetAddress"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json" 
    }

    response = requests.get(url, headers=headers, verify=False)
    user_data = response.json()
    return user_data 

def get_fedex_token(): 
    client_id = os.getenv("FEDEX_API_KEY")
    client_secret = os.getenv("FEDEX_SECRET_KEY")

    url = "https://apis-sandbox.fedex.com/oauth/token"

    data = {
        "grant_type": "client_credentials", 
        "client_id": client_id, 
        "client_secret": client_secret,
    }

    response = requests.post(url, data=data, verify=False)

    with open("fedex_debug_log.txt", "w") as f:
        f.write(f"CLIENT_ID: {client_id}\n")
        f.write(f"CLIENT_SECRET: {client_secret}\n")
        f.write(f"STATUS CODE: {response.status_code}\n")
        f.write(f"RAW RESPONSE: {response.text}\n") 

    fedex_token = response.json()
    return fedex_token["access_token"] 

def validate_address(street, city, state, zip_code, country, token): 
    url = "https://apis-sandbox.fedex.com/address/v1/addresses/resolve" 

    headers = {
        "Authorization": f"Bearer {token}", 
        "Content-Type": "application/json"
    }

    body = {
        "addressesToValidate": [
            {
                "address": {
                    "streetLines": [street],
                    "city": city,
                    "stateOrProvinceCode": state, 
                    "postalCode": zip_code,
                    "countryCode": country
                }
            }
        ]
    }

    with open("outgoing_body_log.txt", "w") as f:
        f.write(f"BODY SENT: {body}\n") 


    response = requests.post(url, headers=headers, json=body, verify=False) 
    return response.json()

def parse_address(full_address): 
    parts = full_address.split(",")

    street = parts[0].strip()
    city = parts[1].strip()
    state_zip = parts[2].strip()

    state_zip_parts = state_zip.split(" ")
    print("STATE_ZIP:", state_zip)
    print("SPLIT RESULT:", state_zip_parts)
    state = state_zip_parts[0]
    zip_code = state_zip_parts[1]

    country = "US" 

    return {
        "street": street,
        "city": city,
        "state": state,
        "zip_code": zip_code, 
        "country": country 
    }

def create_shipment(shipper_name, shipper_address, recipient_name, recipient_address, token): 
    url = "https://apis-sandbox.fedex.com/ship/v1/shipments"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json" 
    }

    body = {
        "labelResponseOptions": "URL_ONLY",
        "requestedShipment": {
            "shipper": {
                "contact": {
                    "personName": shipper_name, 
                    "phoneNumber": "000000000"
                },
                "address": {
                    "streetLines": [shipper_address["street"]],
                    "city": shipper_address["city"],
                    "stateOrProvinceCode": shipper_address["state"],
                    "postalCode": shipper_address["zip_code"],
                    "countryCode": "US" 
                }
            },
            "recipients": [
                {
                    "contact": {
                        "personName": recipient_name,
                        "phoneNumber": "000000000"
                    },
                    "address": {
                        "streetLines": [recipient_address["street"]],
                        "city": recipient_address["city"],
                        "stateOrProvinceCode": recipient_address["state"],
                        "postalCode": recipient_address["zip_code"],
                        "countryCode": "US"
                        }
                    }
            ],
            "serviceType": "PRIORITY_OVERNIGHT",
            "packagingType": "YOUR_PACKAGING",
            "pickupType": "DROPOFF_AT_FEDEX_LOCATION",
            "shippingChargesPayment": {
                "paymentType": "SENDER" 
            },
            "labelSpecification": {
                "labelFormatType": "COMMON2D",
                "imageType": "PDF",
                "labelStockType": "PAPER_85X11_TOP_HALF_LABEL"
            },
            "requestedPackageLineItems": [
                {
                    "weight": {
                        "units": "LB",
                        "value": 10
                    }
                }
            ]
        },
        "accountNumber": {
            "value": os.getenv("FEDEX_ACCOUNT_NUMBER")
        }
    }

    response = requests.post(url, headers=headers, json=body, verify=False)
    return response.json()

def extract_shipment_info(result):
    shipment = result["output"]["transactionShipments"][0]
    tracking_number = shipment["masterTrackingNumber"]
    label_url = shipment["pieceResponses"][0]["packageDocuments"][0]["url"]

    return {
        "trackingNumber": tracking_number,
        "labelUrl": label_url
    }

app = Flask(__name__)

@app.route("/hello")
def hello():
    return "Hello!"

@app.route("/greet", methods=["POST"])
def greet():
    data = request.get_json()
    name = data["name"]
    return jsonify({"message": f"Hello, {name}!"})

@app.route("/joke")
def joke():
    response = requests.get("https://official-joke-api.appspot.com/random_joke", verify=False)
    joke_data = response.json()
    return jsonify(joke_data)

@app.route("/test-secret")
def test_secret():
    return greeting

@app.route("/test-token")
def test_token():
    token = get_graph_token()
    return token

@app.route("/test-address")
def test_address(): 
    token = get_graph_token()
    result = get_user_address("testuserAD@medicalguardian.com", token)
    return jsonify(result)

@app.route("/test-fedex")
def fedex_api():
    token = get_fedex_token()
    return token

@app.route("/test-parse")
def test_parse():
    fake_address = "123 MedicalGuardian Ln, Springfield, PA 18900, US" 
    result = parse_address(fake_address)

    return jsonify(result) 
@app.route("/test-full-chain")
def test_full_chain():
    graph_token = get_graph_token()
    user_data = get_user_address("testuserAD@medicalguardian.com", graph_token)
    raw_address = user_data["streetAddress"]

    with open("chain_debug_log.txt", "w") as f:
        f.write(f"RAW ADDRESS: {raw_address}\n")

    parsed = parse_address(raw_address)

    fedex_token = get_fedex_token()
    result = validate_address(
        parsed["street"],
        parsed["city"],
        parsed["state"],
        parsed["zip_code"],
        parsed["country"],
        fedex_token
    )

    return jsonify(result)

@app.route("/test-create-shipment")
def test_create_shipment():
    graph_token = get_graph_token()

    recipient_data = get_user_address("testuserAD@medicalguardian.com", graph_token)
    recipient_name = recipient_data["displayName"]
    recipient_address = parse_address(recipient_data["streetAddress"])

    shipper_data = get_user_address("aaditya.ramesh@medicalguardian.com", graph_token)

    with open("shipper_debug_log.txt", "w") as f:
        f.write(f"SHIPPER DATA: {shipper_data}\n")

    shipper_name = shipper_data["displayName"]
    shipper_address = parse_address(shipper_data["streetAddress"])

    fedex_token = get_fedex_token()

    result = create_shipment(shipper_name, shipper_address, recipient_name, recipient_address, fedex_token)

    extracted = extract_shipment_info(result)
    return jsonify(extracted)

@app.route("/create-label", methods=["POST"])
def create_label():
    data = request.get_json()
    new_user_email = data["newUserEmail"]

    shipper_name = "INFRASTRUCTURE TEAM MEDICAL GUARDIAN"
    shipper_address = {
        "street": "1818 MARKET ST 12TH FLOOR",
        "city": "PHILADELPHIA",
        "state": "PA",
        "zip_code": "19103"
    }

    graph_token = get_graph_token()
    recipient_data = get_user_address(new_user_email, graph_token)
    recipient_name = recipient_data["displayName"]
    recipient_address = parse_address(recipient_data["streetAddress"])

    fedex_token = get_fedex_token()
    result = create_shipment(shipper_name, shipper_address, recipient_name, recipient_address, fedex_token)

    extracted = extract_shipment_info(result)
    return jsonify(extracted)

if __name__ == "__main__":
    app.run(debug=True)

