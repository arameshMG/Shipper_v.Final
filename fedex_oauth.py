import requests
import config
from debug_utils import debug_log

def get_fedex_token():
    url = "https://apis-sandbox.fedex.com/oauth/token"

    data = {
        "grant_type": "client_credentials",
        "client_id": config.FEDEX_API_KEY,
        "client_secret": config.FEDEX_SECRET_KEY,
    }

    response = requests.post(url, data=data, verify=False)
    token_data = response.json()
    return token_data["access_token"]

def parse_address(full_address):
    parts = full_address.split(",")

    street = parts[0].strip()
    city = parts[1].strip()
    state_zip = parts[2].strip()

    state_zip_parts = state_zip.split(" ")
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
    debug_log("Creating shipment", shipper=shipper_name, recipient=recipient_name)
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
            "value": config.FEDEX_ACCOUNT_NUMBER
        }
    }

    response = requests.post(url, headers=headers, json=body, verify=False)
    debug_log("Shipment API response", result=response.json())
    return response.json()

def extract_shipment_info(result):
    shipment = result["output"]["transactionShipments"][0]
    tracking_number = shipment["masterTrackingNumber"]
    label_url = shipment["pieceResponses"][0]["packageDocuments"][0]["url"]

    return {
        "trackingNumber": tracking_number ,
        "labelUrl": label_url 
    }

