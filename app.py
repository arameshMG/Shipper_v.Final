from flask import Flask, request, jsonify
import graph_client
import fedex_oauth

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

    graph_token = graph_client.get_graph_token()
    recipient_data = graph_client.get_user_address(new_user_email, graph_token)
    recipient_name = recipient_data["displayName"]
    recipient_address = fedex_oauth.parse_address(recipient_data["streetAddress"])

    fedex_token = fedex_oauth.get_fedex_token()
    result = fedex_oauth.create_shipment(
        SHIPPER_NAME, SHIPPER_ADDRESS, recipient_name, recipient_address, fedex_token
    )

    extracted = fedex_oauth.extract_shipment_info(result)
    return jsonify(extracted)

if __name__ == "__main__":
    app.run(debug=True)

