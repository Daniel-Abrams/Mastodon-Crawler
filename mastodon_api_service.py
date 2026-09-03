import requests
import os
import json
from dotenv import load_dotenv
import os
from mastodon import Mastodon




class MastodonAPIService:
    
    def __init__(self):
        load_dotenv()
        self.mastodon = Mastodon(access_token=os.getenv("mastodon_API_ACCESS_TOKEN"), api_base_url = "https://mastodon.au")

    def getAccessToken():
        load_dotenv()
        API_key = os.getenv("mastodon_API_KEY")
        API_secret = os.getenv("mastodon_API_SECRET")
        redirect_uri = os.getenv("mastodon_REDIRECT_URI")
        response = requests.post(
            "https://mastodon.au/oauth/token",
            data={
                "client_id": API_key,
                "client_secret": API_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "client_credentials",
            }
        )
        
        os.environ["mastodon_API_ACCESS_TOKEN"] = json.loads(response.text)["access_token"]
        print(json.loads(response.text))
        
    def searchTimelineHashtag(self, hashtag: str, limit=100):
        statuses = self.mastodon.timeline_hashtag(hashtag=hashtag, limit=40)
        ctr = 0

        while statuses:
            for status in statuses:
                yield status
                ctr += 1
                if ctr >= limit:
                    print(f"Found {limit} results for statuses containing #{hashtag}")
                    return
            statuses = self.mastodon.fetch_next(statuses)
        
        print(f"Found {ctr} results for statuses containing #{hashtag}")
            
    def search(self, query : str, type = "hashtags"):
        return self.mastodon.search_v2(q=query)
    
    def getStatus(self, status_id):
        return self.mastodon.status(status_id)
    
    def getAccountId(self, username):
        return self.mastodon.account_search(username, limit=1)[0]
    
    def getStatusesByAccountName(self,username, start_date, end_date):
        user_account = self.mastodon.account_search(username, limit=1)
        if user_account:
            self.getStatusesByAccount(user_account[0].id, start_date, end_date)

    def getStatusesByAcocuntID(self, id, start_date, end_date):
        statuses = self.mastodon.account_statuses(id, limit=20)
        statuses[0]
        result = []
        while statuses:
            for status in statuses:
                if start_date <= status.created_at <= end_date:
                    result.append(status)
                elif start_date > status.created_at:
                    return result
            statuses = self.mastadon.fetch_next(statuses)

        return result
    
    def getReplies(self, status_id):
        context = self.mastodon.status_context(status_id)
        return context["descendants"]