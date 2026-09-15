from mastodon_api_service import MastodonAPIService
import json
import networkx as nx
from collections import defaultdict
import itertools

flowerBox = "--------------------------------------------------------------------"

class Grapher:
    users = []
    statuses = []
    user_post_map = defaultdict(set)
    seed_users = {}
    
    def __init__(self):
            self.mastodon_api_service = MastodonAPIService()
            self.loadUsers()
            self.loadStatuses()
            
    def loadUsers(self):
        with open("users.json", "r") as file:
            self.users = json.load(file)
            
    def loadStatuses(self):
        with open("statuses.json", "r") as file:
            self.statuses = json.load(file)
            for status in self.statuses:
                self.user_post_map[status['user_id']].add(status['id'])
                
    def constructInfoDiffusionNetwork(self):
        
        info_diffusion_net = nx.DiGraph()
        for status in self.statuses:
            info_diffusion_net.add_node(status['id'], status)
        
        self.addStatusEdges(info_diffusion_net)
        self.saveGraph(info_diffusion_net, "information_diffusion_network_LAFires")
    
        
    def addStatusEdges(self, graph: nx.DiGraph):
        
        for node in graph.nodes():
            status = self.mastodon_api_service.getStatus(node['id'])
            if status.in_reply_to_id and status.in_reply_to_id in graph:
                graph.add_edge(status.in_reply_to_id, status.id, "prompts reply")
            if status.reblog and status.reblog.id in graph:
                graph.add_edge(status.reblog.id, status.id, "reblog")
        
    def constructUserGraph(self):
        user_network = nx.Graph()
        
        for user in self.users():
            user_network.add_node(user['id'], user)
        self.addUserEdges(user_network)
        self.saveGraph(user_network, "user_network_LAFires")
    
    def addUserEdges(self, graph: nx.DiGraph):
        for user1, user2 in list(itertools.combinations(graph.nodes(), 2)):
            if self.follows(user1['id'], user2['id']) and self.follows(user2['id'], user1['id']):
                graph.add_edge(user1['id'], user2['id'], 'friend')
            
    def follows(user1, user2) -> bool:
        return user2 in MastodonAPIService.getFollowees(user1)
        
    
    def saveGraph(graph, name):
        nx.write_graphml(graph, f"{name}.graphml")
    
