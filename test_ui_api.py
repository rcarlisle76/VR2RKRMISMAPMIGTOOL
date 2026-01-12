"""
Test script to inspect UI API response structure for page layouts.
"""

import json
from src.core.credentials import CredentialManager
from src.connectors.salesforce.auth import SalesforceAuthenticator
import requests

# Authenticate
creds = CredentialManager.get_credentials("migration@riskonnect.com")
if not creds:
    print("No saved credentials found")
    exit(1)

sf_instance, error = SalesforceAuthenticator.authenticate(creds)

if not sf_instance:
    print(f"Auth failed: {error}")
    exit(1)

print("[OK] Authenticated successfully")

# Test UI API call for Claim__c
object_name = "Claim__c"
url = f"{sf_instance.base_url}ui-api/object-info/{object_name}"
headers = {
    "Authorization": f"Bearer {sf_instance.session_id}",
    "Content-Type": "application/json"
}

print(f"\nFetching UI API data from: {url}")
response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()

    # Save full response for inspection
    with open("ui_api_response.json", "w") as f:
        json.dump(data, f, indent=2)
    print("[OK] Saved full response to ui_api_response.json")

    # Print structure summary
    print("\n=== Response Structure ===")
    print(f"Keys: {list(data.keys())}")

    if 'recordTypeInfos' in data:
        print(f"\nRecord Types: {list(data['recordTypeInfos'].keys())}")

        # Check first record type structure
        first_rt_id = list(data['recordTypeInfos'].keys())[0]
        rt_info = data['recordTypeInfos'][first_rt_id]
        print(f"\nFirst Record Type ({first_rt_id}) structure:")
        print(f"  Keys: {list(rt_info.keys())}")

        if 'layout' in rt_info:
            print(f"\n  Layout structure:")
            print(f"    Keys: {list(rt_info['layout'].keys())}")
else:
    print(f"Error: {response.text}")
