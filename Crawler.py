from mastadon_api_service import MastadonAPIService
import networkx as nx


class Crawler:
    
    def __init__(self):
            self.mastadon_api_service = MastadonAPIService()
            
    def crawlKeywords(self, keywords: list[str]):
        infomation_diffiusion_network = nx.DiGraph()
        
        for keyword in keywords:
            self.crawlThroughKeyword(graph=infomation_diffiusion_network, keyword=keyword)
        
        print(infomation_diffiusion_network)

    def crawlThroughKeyword(self, graph, keyword: str):
        print(keyword)
        searchResult = self.mastadon_api_service.search(query=keyword)
        for status in searchResult.statuses:
            if status.id not in graph:
                self.crawlStatus(graph=graph, status=status)

    def crawlStatus(self, graph, status):
        graph.add_node(status.id, status=status)
        replies = self.mastadon_api_service.getReplies(status_id=status.id)

        # Handle Replies
        for reply in replies:
            if reply.id not in graph:
                new_status = self.mastadon_api_service.getStatus(reply.id)
                self.crawlStatus(graph, new_status)

            graph.add_edge(status.id, reply.id, relationship="reply")
            
        # Hanlde Parent Post
        if status.in_reply_to_id:
            if status.in_reply_to_id not in graph:
                new_status = self.mastadon_api_service.getStatus(status.in_reply_to_id)
                self.crawlStatus(graph, new_status)
            
            graph.add_edge(status.in_reply_to_id, status.id, relationship="reply")
        
        # Handle If Reblog
        if status.reblog:
            if status.reblog.id not in graph:
                new_status = self.mastadon_api_service.getStatus(status.reblog.id)
                self.crawlStatus(graph, new_status)
            graph.add_edge(status.reblog.id, status.id, type="reblog")
