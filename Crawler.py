import json

from mastodon import MastodonAPIError
from datetime import datetime, timezone
from collections import defaultdict

from mastodon_api_service import MastodonAPIService

# Approximate timeline of the LA wildfires + some time after
start = datetime(2025, 1, 7, tzinfo=timezone.utc)
end = datetime(2025, 3, 31, tzinfo=timezone.utc)

flowerBox = "--------------------------------------------------------------------"

class Crawler:
    seed_users = {}
    status_ids = set()
    statuses = []
    user_post_map = defaultdict(set)
    crawled_users_ids = set()
    users = []
        
    def __init__(self):
            self.mastodon_api_service = MastodonAPIService()
            
    def loadStatuses(self):
        with open("statuses.json", "r") as file:
            self.statuses = json.load(file)
            for status in self.statuses:
                self.user_post_map[status['user_id']].add(status['id'])
    
    def loadSeedUsers(self):
        with open("seed_user_candidates.json", "r") as file:
            self.seed_users = json.load(file)                    
    def GetRelevantUsers(self, seedUsers):
        self.loadStatuses()
        
        for id, _ in seedUsers.items():
            self.crawlUser(self.mastodon_api_service.getAccount(id))
        print(f"User crawl completed with {len(self.crawled_users_ids)} users")
        self.serializeUsers()
        
    def crawlUser(self, user):   
        print(f"Crawling user with id: {user.id} and username: {user.username}")
        if user.id not in self.crawled_users_ids:
            self.crawled_users_ids.add(user.id) 
            self.users.append(user)
        self.serializeUsers()  
        if user.id in self.user_post_map:
            for status_id in self.user_post_map[user.id]:
                print(f"looking at post {status_id} from user {user.username}")
                status = self.mastodon_api_service.getStatus(status_id)
                
                print(f"looking at mentions in {status_id} from user {user.username}")
                for mention in status.mentions:
                    try:
                        if mention.id not in self.crawled_users_ids:
                            self.crawlUser(self.mastodon_api_service.getAccount(mention.id))
                    except MastodonAPIError:
                        print(f"Could not resolve user with id {mention.id}")
            
            for follower in self.mastodon_api_service.getFollowers(user.id):
                if follower in self.user_post_map and follower not in self.crawled_users_ids:
                    self.crawlUser(self.mastodon_api_service.getAccount(follower))
            for followee in self.mastodon_api_service.getFollowees(user.id):
                if followee in self.user_post_map and followee not in self.crawled_users_ids:
                    self.crawlUser(self.mastodon_api_service.getAccount(followee))
                        
    def crawlKeywords(self, keywords: list[str]):
        for keyword in keywords:
            self.crawlThroughKeyword(keyword=keyword)
        
        with open("seed_user_candidates.json", "w") as file:
            json.dump((self.seed_users), file, indent=4)
        
        print(f"{len(self.statuses)} total statuses found")
        self.serializeStatuses()
         
    def crawlThroughKeyword(self, keyword: str):
        print(flowerBox)
        print(f"Beginning keyword crawl for: #{keyword}")
        
        for status in self.mastodon_api_service.searchTimelineHashtag(hashtag=keyword, min_id=start, max_id=end, favorite_requirement=0):
            if status.id not in self.status_ids:
                self.visitStatus(status)
                
                # Handle reblogs
                print(f"found at least {status.reblogs_count} reposts for status {status.id}")
                reblogs = self.mastodon_api_service.getReblogs(status.id, status.created_at)
                for reblog in reblogs:
                    self.visitStatus(reblog)
                
                self.serializeStatuses()

    def visitStatus(self, status):
        if status.id not in self.status_ids:
            user = self.mastodon_api_service.getAccount(status.account.id)
            if user.followers_count >= 1000:
                self.seed_users[user.id] = user.acct
            
            # Crawl the Status
            self.statuses.append(status)
            self.status_ids.add(status.id)
            
            # Handle Context
            ancestors, descendants = self.mastodon_api_service.getContext(status.id)
            for ancestor in ancestors:
                if ancestor.id not in self.status_ids:
                    self.status_ids.add(ancestor.id)
                    self.statuses.append(ancestor)
            for descendant in descendants:
                if descendant.id not in self.status_ids:
                    self.status_ids.add(descendant.id)
                    self.statuses.append(descendant)
                
    def serializeStatuses(self):
        simplified_statuses = []
        for status in self.statuses:
            reblog_id = None
            if status.reblog:
                reblog_id = status.reblog.id
        
            simplified_statuses.append({
                        "id" : status.id,
                        "user_id" : status.account.id,
                        "content" : status.content,
                        "tags": status.tags.to_json(),
                        "created_at" : status.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        "in_reply_to_id" : status.in_reply_to_id,
                        "reblog" : reblog_id
                    })

        with open("statuses.json", "w") as f:
            json.dump(simplified_statuses, f, indent=4) 
        
    def serializeUsers(self):
            simplified_users = []
            for user in self.users:
                simplified_users.append({
                            "id" : user.id,
                            "username" : user.username,
                            "followers" : user.followers_count,
                            "following" : user.following_count,
                            "bio" : user.note,
                            "created_at" : user.created_at.strftime("%Y-%m-%d %H:%M:%S")
                        })
    
            with open("users.json", "w") as f:
                json.dump(simplified_users, f, indent=4)   


    def getRelationships(self):
        self.loadStatuses()
        for s in self.statuses:
            print(f"working on id: {s['id']}")
            status = self.mastodon_api_service.getStatus(s['id'])
            if status.in_reply_to_id:
                s['in_reply_to_id'] = status.in_reply_to_id
            else:
                s['in_reply_to_id'] = None
            
            if status.reblog:
                s['reblog'] = status.reblog.id
            else:
                s['reblog'] = None

            with open("statuses.json", "w") as f:
                json.dump(self.statuses, f, indent=4)
                
