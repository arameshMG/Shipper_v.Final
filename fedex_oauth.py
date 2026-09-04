import requests
import re
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

def _parse_structured(raw_address):
    city_state_zip_pattern = re.compile(
        r'(?P<city>[A-Za-z][A-Za-z\s\.\-\']*?)\s*,?\s+(?P<state>[A-Za-z]{2})\s+(?P<zip>\d{5}(-\d{4})?)\s*$'
    )

    lines = [line.strip() for line in raw_address.splitlines() if line.strip()]

    for i, line in enumerate(lines):
        match = city_state_zip_pattern.fullmatch(line) or city_state_zip_pattern.search(line)
        if match and match.start() == 0:
            candidate_lines = lines[:i]
            if candidate_lines:
                city = match.group("city").strip().rstrip(',')
                state = match.group("state").strip().upper()
                zip_code = match.group("zip").strip()
                return {
                    "street": candidate_lines[-1],
                    "city": city,
                    "state": state,
                    "zip_code": zip_code
                }

    flat = raw_address.strip()
    match = city_state_zip_pattern.search(flat)
    if match:
        prefix = flat[:match.start()].strip().rstrip(',').strip()
        if prefix and ',' in prefix:
            city = match.group("city").strip().rstrip(',')
            state = match.group("state").strip().upper()
            zip_code = match.group("zip").strip()
            prefix_parts = [p.strip() for p in prefix.split(',') if p.strip()]
            street = prefix_parts[-1] if prefix_parts else prefix
            if re.search(r'\d', street):
                return {
                    "street": street,
                    "city": city,
                    "state": state,
                    "zip_code": zip_code
                }

    raise ValueError("Not a cleanly structured address")


def _parse_concatenated(raw_address):
    text = raw_address.strip()
    text = re.sub(r'(?<=[a-zA-Z])(?=\d)', ' ', text)
    text = re.sub(r'(?<=\d)(?=[A-Za-z])', ' ', text)
    text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    tokens = text.split(' ')

    street_start_index = None
    for i, tok in enumerate(tokens):
        if re.fullmatch(r'\d+', tok):
            street_start_index = i
            break

    if street_start_index is None:
        raise ValueError(f"Could not find a street number in: {raw_address!r}")

    address_only = ' '.join(tokens[street_start_index:])

    city_state_zip_pattern = re.compile(
        r'(?P<city>[A-Za-z][A-Za-z\s\.\-\']*?)\s*,?\s+(?P<state>[A-Za-z]{2})\s+(?P<zip>\d{5}(-\d{4})?)\s*$'
    )
    match = city_state_zip_pattern.search(address_only)

    if not match:
        raise ValueError(f"Could not find City/State/ZIP in: {raw_address!r}")

    city = match.group("city").strip().rstrip(',').strip()
    state = match.group("state").strip().upper()
    zip_code = match.group("zip").strip()
    street = address_only[:match.start()].strip().rstrip(',').strip()

    if not street:
        raise ValueError(f"No street found before City/State/Zip in: {raw_address!r}")

    return {
        "street": street,
        "city": city,
        "state": state,
        "zip_code": zip_code
    }


def parse_address(raw_address):
    if not raw_address or not raw_address.strip():
        raise ValueError("parse_address() received an empty address")

    raw_address = raw_address.strip().rstrip(',').strip()

    try:
        return _parse_structured(raw_address)
    except ValueError:
        pass

    return _parse_concatenated(raw_address)

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

