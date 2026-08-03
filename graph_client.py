import requests
import config

def get_graph_token():
    url = f"https://login.microsoftonline.com/{config.GRAPH_TENANT_ID}/oauth2/v2.0/token"

    data = {
        "client_id": config.GRAPH_CLIENT_ID,
        "client_secret": config.GRAPH_CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }

    print("TENANT ID:", config.GRAPH_TENANT_ID)
    print("CLIENT ID:", config.GRAPH_CLIENT_ID)
    print("CLIENT SECRET:" config. GRAPH_CLIENT_SECRET)

    response = requests.post(url, data=data, verify=False)

    print("STATUS CODE:", response.status_code)
    print("RAW RESPONSE:", response.text)

    token_data = response.json()
    return token_data["access_token"]


def get_user_address(user_email, token):
    url = f"https://graph.microsoft.com/v1.0/users/{user_email}?$select=displayName, streetAddress"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)
    user_data = response.json()
    return user_data

