import requests
import os
import json
from dotenv import load_dotenv
import os


def getAccessToken():
    load_dotenv()
    API_key = os.getenv("MASTADON_API_KEY")
    API_secret = os.getenv("MASTADON_API_SECRET")
    redirect_uri = os.getenv("MASTADON_REDIRECT_URI")
    response = requests.post(
        "https://mastodon.au/oauth/token",
        data={
            "client_id": API_key,
            "client_secret": API_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "client_credentials",
        }
    )
    
    os.environ["MASTADON_API_ACCESS_TOKEN"] = json.loads(response.text)["access_token"]
    print(json.loads(response.text))

def search(query : str, type = "hashtags"):
    load_dotenv()
    access_token = os.getenv("MASTADON_API_ACCESS_TOKEN")
    response = requests.get(
        "https://mastodon.au/api/v2/search",
        params={
            "q": query,
            "type": type
        },
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )
    print(response.status_code)
    return json.loads(response.text)