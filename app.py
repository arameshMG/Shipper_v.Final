from flask import Flask, request, jsonify
import graph_client
import fedex_oauth
from debug_utils import debug_log

app = Flask(__name__)

SHIPPER_NAME = "INFRASTRUCTURE TEAM MEDICAL GUARDIAN"
SHIPPER_ADDRESS = {
    "street": "1818 Market St 12th Floor",
    "city": "Philadelphia",
    "state": "PA",
    "zip_code": "19103"
}

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/create-label", methods=["POST"])
def create_label():
    data = request.get_json()
    new_user_email = data["newUserEmail"]
    print("NEW USER EMAIL:", new_user_email)

    graph_token = graph_client.get_graph_token()
    recipient_data = graph_client.get_user_address(new_user_email, graph_token)
    print("RECIPIENT DATA:", recipient_data)
    recipient_name = recipient_data["displayName"]
    recipient_address = fedex_oauth.parse_address(recipient_data["streetAddress"])

    fedex_token = fedex_oauth.get_fedex_token()
    result = fedex_oauth.create_shipment(
        SHIPPER_NAME, SHIPPER_ADDRESS, recipient_name, recipient_address, fedex_token
    )

    print("FEDEX RESULT:", result)

    extracted = fedex_oauth.extract_shipment_info(result)
    return jsonify(extracted)

@app.route("/create-labels", methods=["POST"])
def create_labels():
    data = request.get_json()
    debug_log("Request received", body=data)
    user_email = data["userEmail"]
    debug_log("Extracted user_email", user_email=user_email)
    print("USER EMAIL:", user_email)

    graph_token = graph_client.get_graph_token()
    user_data = graph_client.get_user_address(user_email, graph_token)
    debug_log("Graph user lookup result", user_data=user_data)
    print("User DATA:", user_data)
    user_name = user_data["displayName"]
    user_address = fedex_oauth.parse_address(user_data["streetAddress"])

    fedex_token = fedex_oauth.get_fedex_token()

# Outbound

    outbound_result = fedex_oauth.create_shipment(
        SHIPPER_NAME, SHIPPER_ADDRESS, user_name, user_address, fedex_token
    )
    debug_log("FedEx outbound result", outbound_result=outbound_result)
    print("OUTBOUND RESULT:", outbound_result)
    outbound_extracted = fedex_oauth.extract_shipment_info(outbound_result)

# Inbound

    inbound_result = fedex_oauth.create_shipment(
        user_name, user_address, SHIPPER_NAME, SHIPPER_ADDRESS, fedex_token
    )
    debug_log("FedEx return result", inbound_result=inbound_result)
    print("RETURN RESULT:", inbound_result)
    return_extracted = fedex_oauth.extract_shipment_info(inbound_result)

    return jsonify({
        "outboundLabel": outbound_extracted,
        "returnLabel": return_extracted
    })

if __name__ == "__main__":
    app.run(debug=True)
