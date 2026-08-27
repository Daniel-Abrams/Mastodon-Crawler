import requests
import json
# Test public data access

def testAPI():
    response = requests.get("https://mastodon.au/api/v1/timelines/public", params={"limit" : "2"})
    statuses = json.loads(response.text) # this converts the json to a python list of dictionary
    assert statuses[0]["visibility"] == "public" # we are reading a public timeline
    print(statuses[0]["content"]) # this prints the status text



