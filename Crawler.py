from mastodon_api_service import MastodonAPIService
from mastodon import MastodonAPIError
import json
import networkx as nx
from networkx.readwrite import json_graph
from datetime import datetime, timezone

# Approximate timeline of the australia wildfires
start = datetime(2019, 9, 1, tzinfo=timezone.utc)
end = datetime(2021, 1, tzinfo=timezone.utc)

flowerBox = "--------------------------------------------------------------------"

class Crawler:
    keywords = []
    relevance_keywords = [
        "fire",
        "fires",
        "bushfire",
        "bushfires",
        "wildfire",
        "rescue",
        "evacuate",
        "evacuation",
        "firefighter",
        "firefighters",
        "smoke",
        "burning",
        "wildlife",
        "koala",
        "kangaroo",
        "emergency",
        "shelter",
        "donate",
        ]
    
    def __init__(self):
            self.mastodon_api_service = MastodonAPIService()
    
    def crawlUsers(self, seedUsers):
        user_graph = nx.DiGraph()
        
        for user in seedUsers:
            self.crawlUsers(user_graph, self.mastodon_api_service.getAccountId(user))

        print(user_graph.number_of_nodes())
        
    def crawlUser(self, graph, user):
        statuses = self.mastodon_api_service.getStatusesByAccountID(user.id, start_date=start, end_date=end)
        graph.add_node(user.id, user=user)
        
        for status in statuses:
            if self.isStatusRelevant(status):
                for mention in status.mentions:
                    try:
                        if mention.id not in graph:
                            self.crawlUser(graph,mention.id)
                        graph.add_edge(user.id, mention.id, "mentions")
                    except MastodonAPIError:
                        print(f"Could not resolve user with id {mention.id}")
                        
                
    def isStatusRelevant(self, status):
        for relevant_word in self.relevance_keywords:
            if relevant_word in status.content:
                 return True
        for keyword in self.keywords:
            if keyword in status.tags:
                return True
        
        return False   
            
    def crawlKeywords(self, keywords: list[str]):
        infomation_diffiusion_network = nx.DiGraph()
        self.keywords = keywords
        for keyword in keywords:
            self.crawlThroughKeyword(graph=infomation_diffiusion_network, keyword=keyword)
            
        self.serliazeStatusGraph(infomation_diffiusion_network)
        
    def crawlThroughKeyword(self, graph, keyword: str):
        
        print(flowerBox)
        print(f"Beginning keyword crawl for: #{keyword}")
        
        for status in self.mastodon_api_service.searchTimelineHashtag(hashtag=keyword):
            if status.id not in graph:
                self.crawlStatus(graph=graph, status=status)
            
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

    def crawlStatus(self, graph, status):
        graph.add_node(status.id, status=status)

        # Collect relevant keywords for later
        for tag in status.tags:
            self.relevant_kewords.add(tag.name)
            
        # Handle Replies
        replies = self.mastodon_api_service.getReplies(status_id=status.id)
        for reply in replies:
            try:
                if reply.id not in graph: 
                    new_status = self.mastodon_api_service.getStatus(reply.id)
                    self.crawlStatus(graph, new_status)
                graph.add_edge(status.id, reply.id, relationship="reply")
            except MastodonAPIError:
                print(f"Could not retrieve reply {reply.id}")
            
        # Hanlde Parent Post
        if status.in_reply_to_id:
            try:
                if status.in_reply_to_id not in graph:
                    new_status = self.mastodon_api_service.getStatus(status.in_reply_to_id)
                    self.crawlStatus(graph, new_status)
                graph.add_edge(status.in_reply_to_id, status.id, relationship="reply")
            except MastodonAPIError:
                print(f"Could not retrieve parent {status.in_reply_to_id}")
        
        # Handle If Reblog
        if status.reblog:
            try:
                if status.reblog.id not in graph:
                    new_status = self.mastodon_api_service.getStatus(status.reblog.id)
                    self.crawlStatus(graph, new_status)
                graph.add_edge(status.reblog.id, status.id, type="reblog")
            except MastodonAPIError:
                print(f"Could not retrieve original post with id {status.reblog.id}")
