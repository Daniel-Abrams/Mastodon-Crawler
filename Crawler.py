from mastodon_api_service import MastodonAPIService
from mastodon import MastodonAPIError
import json
import networkx as nx
from datetime import datetime, timezone
from collections import defaultdict

# Approximate timeline of the australia wildfires
start = datetime(2025, 1, 1, tzinfo=timezone.utc)
end = datetime(2025, 6, 30, tzinfo=timezone.utc)

flowerBox = "--------------------------------------------------------------------"

class Crawler:
    user_post_map = defaultdict(set)
    depth_limit = 80
    keywords = []
    seed_users = {}
    
    def __init__(self):
            self.mastodon_api_service = MastodonAPIService()
            
    def loadStatuses(self):
        with open("status_graph.json", "r") as file:
            status_graph = json.load(file)
            for node in status_graph['nodes']:
                self.user_post_map[node['user_id']].add(node['id'])
    
    def crawlUsers(self, seedUsers):
        user_graph = nx.DiGraph()
        self.loadStatuses()
        
        for id, _ in seedUsers.items():
            self.crawlUser(user_graph, self.mastodon_api_service.getAccount(id))
        print(user_graph.number_of_nodes())
        
    def crawlUser(self, graph, user):
        print(f"Crawling user with id: {user.id} and username: {user.username}")
        graph.add_node(user.id, user=user)
        statuses = self.mastodon_api_service.getStatusesByAccountID(user.id, start_date=start, end_date=end)
        
        followers = self.mastodon_api_service.getFollowers(user)
        follower_ids = {follower.id for follower in followers}
        
        for status in statuses:
            if self.isStatusRelevant(status):
                replies = self.mastodon_api_service.getReplies(status_id=status.id)
                for mention in status.mentions:
                    try:
                        if mention.id not in graph:
                            self.crawlUser(graph,mention)
                        graph.add_edge(user.id, mention.id, relationship="mentions")
                    except MastodonAPIError:
                        print(f"Could not resolve user with id {mention.id}")
                for reply in replies:
                    try:
                        if self.isUserRelevant(reply.account) and reply.account.id in follower_ids:
                            self.crawlUser(graph, reply.account)
                            graph.add_edge(reply.account.id, user.id, relationship="follows")
                    except MastodonAPIError:
                            print(f"Could not resolve user with id {reply.account.id}")
                        
        
        for follower in self.mastodon_api_service.getFollowers(user.id):
            if follower.followers_count >= 0.25 * user.followers_count:
                if follower.id not in graph and self.isUserRelevant(user):    
                    self.crawlUser(graph, follower)
                graph.add_edge(follower.id, user.id, relationship="follows")
                        
    def isUserRelevant(self, user):
        if user.id in self.user_post_map:
            return True
        return False
    
    def isStatusRelevant(self, status):
        content = status.content.lower()

        has_fire_term = any(
            keyword in content
            for keyword in ["fire", "fires", "wildfire", "wildfires"]
        )

        has_location = any(
            keyword in content
            for keyword in ["los angeles","california","altadena","pasadena","malibu","palisades","eaton"]
        )

        has_emergency_term = any(
            keyword in content 
            for keyword in ["evacuation","evacuate","firefighter","rescue","smoke","shelter"]
            )
        
        has_relevant_hashtag = any(
            hashtag in status.tags
            for hashtag in self.keywords
        )

        return (has_fire_term and (has_location or has_emergency_term)) or has_relevant_hashtag 
            
    def crawlKeywords(self, keywords: list[str]):
        infomation_diffiusion_network = nx.DiGraph()
        self.keywords = keywords
        for keyword in keywords:
            self.crawlThroughKeyword(graph=infomation_diffiusion_network, keyword=keyword)
        
        print(infomation_diffiusion_network.number_of_nodes())
        self.serliazeStatusGraph(infomation_diffiusion_network)
        with open("seed_users.json", "w") as file:
            json.dump(json.dumps(self.seed_users), file)
         
    def crawlThroughKeyword(self, graph, keyword: str):
    
        print(flowerBox)
        print(f"Beginning keyword crawl for: #{keyword}")
        
        for status in self.mastodon_api_service.searchTimelineHashtag(hashtag=keyword, min_id=start, max_id=end, favorite_requirement=2 ):
            if status.id not in graph:
                # Check if user is a seed user candidate, which we define as having at least 750 followers
                user = self.mastodon_api_service.getAccount(status.account.id)
                if user.followers_count >= 750:
                    self.seed_users[user.id] = user.acct
                
                # Crawl the Status
                self.crawlStatus(graph=graph, status=status, depth=0)
                
            
        print("Status crawl finished")
        print(flowerBox)
        
    def serliazeStatusGraph(seflf, graph):
        data = nx.node_link_data(graph)
        for node in data["nodes"]:
            status = node.pop("status")
            node.update(
                            {
                                "id" : status.id,
                                "user_id" : status.account.id,
                                "content" : status.content
                            }       
                        )

        with open("status_graph.json", "w") as f:
            json.dump(data, f, indent=4)

    def crawlStatus(self, graph, status, depth):
        #print(f"new depth: {depth}")
        graph.add_node(status.id, status=status)

        if depth < self.depth_limit:
            # Handle Replies
            replies = self.mastodon_api_service.getReplies(status_id=status.id)
            for reply in replies:
                try:
                    if reply.id not in graph: 
                        self.crawlStatus(graph, reply, depth + 1)
                    graph.add_edge(reply.in_reply_to_id, reply.id, relationship="reply")
                except MastodonAPIError:
                    print(f"Could not retrieve reply {reply.id}")
                
            # Hanlde Parent Post
            if status.in_reply_to_id:
                try:
                    if status.in_reply_to_id not in graph:
                        new_status = self.mastodon_api_service.getStatus(status.in_reply_to_id)
                        self.crawlStatus(graph, new_status, depth + 1)
                    graph.add_edge(status.in_reply_to_id, status.id, relationship="reply")
                except MastodonAPIError:
                    print(f"Could not retrieve parent {status.in_reply_to_id}")
            
            # Handle If Reblog
            if status.reblog:
                try:
                    if status.reblog.id not in graph:
                        self.crawlStatus(graph, status.reblog, depth + 1)
                    graph.add_edge(status.reblog.id, status.id, type="reblog")
                except MastodonAPIError:
                    print(f"Could not retrieve original post with id {status.reblog.id}")
