import requests
import os
import json
import os
import datetime

from mastodon import Mastodon
from mastodon.return_types import *
from dotenv import load_dotenv
from collections import defaultdict
from typing import Any
from datetime import datetime, timedelta

from project1.config import *

class MastodonAPIService:
    
    user_cache = {}
    status_cache = {}
    followers = {}
    followees = {}
    reposts = {}
    reply_dict: defaultdict[str, list[Any]] = defaultdict(list)
    
    def __init__(self):
        load_dotenv(PROJECT_ROOT / ".env", override=True)
        self.loadReposts()
        self.loadRelationships()
        self.mastodon = Mastodon(access_token=os.getenv("MASTODON_API_ACCESS_TOKEN"), api_base_url = "https://mastodon.social")
        print(os.getenv("mastodon_API_KEY"))
        self.mastodon.account_verify_credentials()

    def getAccessToken():
        load_dotenv(PROJECT_ROOT / ".env", override=True)
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
        print(f"Access token: {json.loads(response.text)["access_token"]}")
        
    def searchTimelineHashtag(self, hashtag: str, min_id, max_id, limit=20):
        statuses = self.mastodon.timeline_hashtag(hashtag=hashtag, min_id=min_id, max_id=max_id, limit=40)
        ctr = 0
        res = []
        while statuses:
            for status in statuses:
                if status.replies_count > 10 or status.reblogs_count > 5:
                    res.append(status)
                    ctr += 1
                if ctr >= limit:
                    print(f"Found {limit} results for statuses containing #{hashtag}")
                    return res
            statuses = self.mastodon.fetch_next(statuses)
        
        print(f"Found {ctr} results for statuses containing #{hashtag}")
        return res
            
    def search(self, query: str, min_id, max_id, limit=200, type = "hashtags"):
        return self.mastodon.search_v2(q=query, min_id=min_id, max_id=max_id, type=type, limit=limit)
    
    def getStatus(self, status_id) -> Status:
        if status_id in self.status_cache:
            return self.status_cache[status_id]
        else:
            status = self.mastodon.status(status_id)
            self.status_cache[status_id] = status
            if status.reblog:
                self.status_cache[status.reblog.id] = status.reblog
            return status
    
    def getAccountId(self, username):
        return self.mastodon.account_search(username, limit=1)[0]
    
    def getStatusesByAccountName(self,username, start_date, end_date):
        user_account = self.mastodon.account_search(username, limit=1)
        if user_account:
            return self.getStatusesByAccount(user_account[0].id, start_date, end_date)

    def getStatusesByAccountID(self, id, start_date, end_date, limit=20):
        cache_key = (id, start_date, end_date)

        if cache_key in self.status_cache:
            return self.status_cache[cache_key]

        self.status_cache[cache_key] = []

        statuses = self.mastodon.account_statuses(id,min_id=start_date,max_id=end_date,limit=limit)


        for status in statuses:
            self.status_cache[cache_key].append(status)
        return self.status_cache[cache_key]
    
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
    
    def getContext(self, status_id):
        context = self.mastodon.status_context(status_id)
        for status in context["descendants"]:
            self.status_cache[status.id] = status
            self.reply_dict[status.in_reply_to_id].append(status)
        for status in context["ancestors"]:
            self.status_cache[status.id] = status
        return context.ancestors, context.descendants

    def getReblogs(self, status_id, posted: datetime):
        res = []

        if status_id in self.reposts:
            for id in self.reposts[status_id]:
                res.append(self.getStatus(id))
            return res
        
        self.reposts[status_id] = []
        users = self.mastodon.status_reblogged_by(status_id)
        for user in users:
            statuses = self.getStatusesByAccountID(user.id, start_date=posted, end_date=posted + timedelta(days=1))
            for status in statuses:
                if status.reblog and status.reblog.id == status_id:
                    res.append(status)
                    self.reposts[status_id].append(status.id)
        self.saveReposts()
        return res
            
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
                self.followees[id].add(followee.id)
                self.user_cache[followee.id] = followee
            followees = self.mastodon.fetch_next(followees)
        self.saveRelationships()
        return self.followees[id] 
            
    def getFollowers(self, id) -> set:
        if id in self.followers:
            return self.followers[id]
        
        self.followers[id] = set()
        followers = self.mastodon.account_followers(id)
        while followers:
            for follower in followers:
                 self.followers[id].add(follower.id)
                 self.user_cache[follower.id] = follower
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
            
            
        with open(DATA_DIRECTORY / "followers.json", "w") as f:
            json.dump(frozen_followers, f, indent=4)

        with open(DATA_DIRECTORY / "followees.json", "w") as f:
            json.dump(frozen_followees, f, indent=4)  
    
    def loadRelationships(self):
        try:
            with open(DATA_DIRECTORY / "followers.json", "r") as f:
                self.followers = json.load(f)

            for key in self.followers.keys():
                self.followers[key] = set(self.followers[key])
                
            with open(DATA_DIRECTORY / "followees.json", "r") as f:
                self.followees = json.load(f)
            
            for key in self.followees.keys():
                self.followees[key] = set(self.followees[key])
        except Exception:
            pass

    def loadReposts(self):
        print(Path(DATA_DIRECTORY / "reposts.json"))
        with open(DATA_DIRECTORY / "reposts.json", "r") as f:
            self.reposts = json.load(f)
    
    def saveReposts(self):
        with open(DATA_DIRECTORY / "reposts.json", "w") as f:
            json.dump(self.reposts, f, indent=4)