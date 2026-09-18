import requests

AUDIT_SERVICE_URL = "https://audit-service-2k1g.onrender.com"


def log_to_audit(event_type, user_identifier, status, details=None, source_service="shipper-flask-app"):
    try:
        requests.post(f"{AUDIT_SERVICE_URL}/events", json={
            "eventType": event_type,
            "userIdentifier": user_identifier,
            "status": status,
            "details": details,
            "sourceService": source_service
        }, timeout=5, verify=False)
    except Exception as e:
        print(f"Failed to log to audit service (non-fatal): {e}")
