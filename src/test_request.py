import json
import requests


url = "http://127.0.0.1:8000/recommend"

payload = {
    "ticket_id": "T1",
    "ticket_text": "My order was delayed and I need help with the shipping status",
}

response = requests.post(url, json=payload)

print("Recommended Articles:", json.dumps(response.json(), indent=2))
