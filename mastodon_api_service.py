import requests
import os
import json
from dotenv import load_dotenv
import os
from mastodon import Mastodon
from mastodon.return_types import *

from collections import defaultdict
from typing import Any


class MastodonAPIService:
    
    user_cache = {}
    status_cache = {}
    followers = {}
    followees = {}
    reply_dict: defaultdict[str, list[Any]] = defaultdict(list)
    
    def __init__(self):
        load_dotenv()
        self.loadRelationships()
        self.mastodon = Mastodon(access_token=os.getenv("MASTODON_API_ACCESS_TOKEN"), api_base_url = "https://mastodon.social")
        self.mastodon.account_verify_credentials()

    def getAccessToken():
        load_dotenv()
        API_key = os.getenv("mastodon_API_KEY")
        API_secret = os.getenv("mastodon_API_SECRET")
        redirect_uri = os.getenv("mastodon_REDIRECT_URI")
        response = requests.post(
            "https://mastodon.social/oauth/token",
            data={
                "client_id": API_key,
                "client_secret": API_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "client_credentials",
            }
        )
        
        os.environ["mastodon_API_ACCESS_TOKEN"] = json.loads(response.text)["access_token"]
        print(json.loads(response.text))
        
    def searchTimelineHashtag(self, hashtag: str, min_id, max_id, limit=200, favorite_requirement=0):
        statuses = self.mastodon.timeline_hashtag(hashtag=hashtag, min_id=min_id, max_id=max_id, limit=40)
        ctr = 0
        res = []
        while statuses:
            for status in statuses:
                status.tags.to_json
                if status.favourites_count >= favorite_requirement:
                    res.append(status)
                    ctr += 1
                if ctr >= limit:
                    print(f"Found {limit} results for statuses containing #{hashtag}")
                    return res
            statuses = self.mastodon.fetch_next(statuses)
        
        print(f"Found {ctr} results for statuses containing #{hashtag}")
        return res
            
    def search(self, query : str, type = "hashtags"):
        return self.mastodon.search_v2(q=query)
    
    def getStatus(self, status_id) -> Status:
        if status_id in self.status_cache:
            return self.status_cache[status_id]
        return self.mastodon.status(status_id)
    
    def getAccountId(self, username):
        return self.mastodon.account_search(username, limit=1)[0]
    
    def getStatusesByAccountName(self,username, start_date, end_date):
        user_account = self.mastodon.account_search(username, limit=1)
        if user_account:
            self.getStatusesByAccount(user_account[0].id, start_date, end_date)

    def getStatusesByAccountID(self, id, start_date, end_date):
        cache_key = (id, start_date, end_date)

        if cache_key in self.status_cache:
            yield from self.status_cache[cache_key]
            return

        self.status_cache[cache_key] = []

        statuses = self.mastodon.account_statuses(id,since_id=None,min_id=start_date,max_id=end_date,limit=40)

        while statuses:
            for status in statuses:
                self.status_cache[cache_key].append(status)
                yield status

            statuses = self.mastodon.fetch_next(statuses)
    
    def getFavorites(self, status_id):
        
        favorites = self.mastodon.status_favourited_by(status_id)
        
        for favorite in favorites:
            self.user_cache[favorite.id] = favorite
        
        return favorites
    
    def getReplies(self, status_id):
        if status_id in self.reply_dict:
            return self.reply_dict[status_id]
        context = self.mastodon.status_context(status_id)
        for status in context["descendants"]:
            self.status_cache[status.id] = status
            self.reply_dict[status.in_reply_to_id].append(status)
        for status in context["ancestors"]:
            self.status_cache[status.id] = status
        return self.reply_dict[status_id]
    
    def getAccount(self, id) -> Account:
        if id in self.user_cache:
            return self.user_cache[id]
        else:
            self.user_cache[id] = self.mastodon.account(id)
            return self.user_cache[id]

    def getFollowees(self, id) -> set:
        if id in self.followees:
            return self.followees[id]
        
        self.followees[id] = set()
        followees = self.mastodon.account_following(id)
        while followees:
            for followee in followees:
                self.followers[id].add(followee.id)
                self.user_cache[followee.id] = followee
            followees = self.mastodon.fetch_next(followees)
        self.saveRelationships()
        return self.followees[id] 
            
    def getFollowers(self, id, max=1000):
        if id in self.followers:
            return self.followers[id]
        
        ctr = 0
        self.followers[id] = set()
        followers = self.mastodon.account_followers(id)
        while followers and ctr <= max:
            for follower in followers:
                 self.followers[id].add(follower.id)
                 self.user_cache[follower.id] = follower
            ctr += len(followers)
            followers = self.mastodon.fetch_next(followers)
        self.saveRelationships()
        return self.followers[id]
    
    def saveRelationships(self):
        frozen_followers = {}
        for key in self.followers.keys():
            frozen_followers[key] = list(self.followers[key])
        
        frozen_followees = {}
        for key in self.followees.keys():
            frozen_followees[key] = list(self.followees[key])
            
            
        with open("followers.json", "w") as f:
            json.dump(frozen_followers, f, indent=4)

        with open("followees.json", "w") as f:
            json.dump(frozen_followees, f, indent=4)  
    
    def loadRelationships(self):
        try:
            with open("followers.json", "r") as f:
                self.followers = json.load(f)

            for key in self.followers.keys():
                self.followers[key] = set(self.followers[key])
                
            with open("followees.json", "r") as f:
                self.followees = json.load(f)
            
            for key in self.followees.keys():
                self.followees[key] = set(self.followees[key])
        except Exception:
            pass
