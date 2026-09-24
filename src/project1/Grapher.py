import json
import networkx as nx
import matplotlib.pyplot as plt
import re
import numpy as np

from PIL import Image
from wordcloud import WordCloud, STOPWORDS
from project1.seeds import keywords
from collections import defaultdict

from project1.mastodon_api_service import MastodonAPIService


flowerBox = "--------------------------------------------------------------------"

class Grapher:
    tag_colors = {}
    users = []
    statuses = []
    user_post_map = defaultdict(set)
    post_user_map = {}
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
                self.post_user_map[status['id']] = status['user_id']
                
    def constructInfoDiffusionNetwork(self):
        self.giveTagColors()
        info_diffusion_net = nx.DiGraph()
        for status in self.statuses:
            status['tags'] = self.sanitizeTags(status['tags'])
            r,g,b = self.blend_colors(status['tags'])
            viz =  {
                    "color": {
                    "r": r,
                    "g": g,
                    "b": b
                    }
                }
            info_diffusion_net.add_node(status['id'], status=status, viz=viz)

        self.addStatusEdges(info_diffusion_net)
        print(f"Finished constructing info diffiusion network with {info_diffusion_net.number_of_nodes()} nodes and {info_diffusion_net.number_of_edges()} edges")
        self.saveGraph(info_diffusion_net, "information_diffusion_network_LAFires")
    
        
    def addStatusEdges(self, graph: nx.DiGraph):
        
        for node in graph.nodes():
            status = self.findStatus(node)
            if status['in_reply_to_id'] and status['in_reply_to_id'] in graph:
                graph.add_edge(status['in_reply_to_id'], status['id'], relationship="prompts_reply")
            if status['reblog'] and status['reblog'] in graph:
                graph.add_edge(status['reblog'], status['id'], relationship="reblog")
        
    def constructUserGraph(self):
        user_network = nx.Graph()
        
        for user in self.users:
            user_network.add_node(user['id'], user=user)
        self.addUserEdges(user_network)
        print(f"Finished constructing user network with {user_network.number_of_nodes()} nodes and {user_network.number_of_edges()} edges")
        self.saveGraph(user_network, "user_network_LAFires")
    
    def addUserEdges(self, graph: nx.Graph):
        for status in self.statuses:
            if status['in_reply_to_id']:
                if status['in_reply_to_id'] in self.post_user_map:
                    origin_user = self.post_user_map[status['in_reply_to_id']]
                    if status['user_id'] in graph and origin_user in graph and origin_user != status['user_id']:
                        graph.add_edge(status['user_id'], origin_user, relationship='interacts')
            if status['reblog']:
                if status['reblog'] in self.post_user_map:
                    origin_user = self.post_user_map[status['reblog']]
                    if status['user_id'] in graph and origin_user in graph and origin_user != status['user_id']:
                        graph.add_edge(status['user_id'], origin_user, relationship='interacts') 
            
    def follows(self, user1, user2) -> bool:
        return user2 in self.mastodon_api_service.getFollowees(user1)
        
    
    def saveGraph(self, graph, name):
        
        nx.write_gexf(graph, f"{name}.gexf")
    

    def findStatus(self, id):
        for status in self.statuses:
            if status['id'] == id:
                return status
    
    def sanitizeTags(self, tags):
        pattern = r'"name": ".*"'
        sanitized_tags = []
        for match in re.finditer(pattern, tags):
            tag = self.longest_match(match.group())
            if tag:
                sanitized_tags.append(tag)
        
        return sanitized_tags
    
    def longest_match(self, tag):
        longest_match = ""
        for keyword in keywords:
            if (keyword.lower() in tag or keyword in tag) and len(keyword) > len(longest_match):
                longest_match = keyword
        
        return longest_match
    
    def giveTagColors(self):
        for keyword in keywords:
            if "palisades" in keyword.lower():
                self.tag_colors[keyword] = (0, 128, 128)       
            elif "altadena" in keyword.lower():
                self.tag_colors[keyword] = (240, 150, 30)       
            elif "eaton" in keyword.lower():
                self.tag_colors[keyword] =  (30, 120, 210)       
            elif "la" in keyword.lower() or "losangeles" in keyword.lower():
                self.tag_colors[keyword] = (150, 50, 190)     
            elif "california" in keyword.lower() or "ca" in keyword.lower():
                self.tag_colors[keyword] = (30, 180, 90)       
            elif "fire" in keyword.lower():
                self.tag_colors[keyword] = (226, 88, 34)
            else:
                self.tag_colors[keyword] = (190, 190, 190)                
    
    def blend_colors(self, tags):
        
        if len(tags) < 1:
            return (190, 190, 190)
        
        r = round(sum(self.tag_colors[tag][0] for tag in tags) / len(tags))
        g = round(sum(self.tag_colors[tag][1] for tag in tags) / len(tags))
        b = round(sum(self.tag_colors[tag][2] for tag in tags) / len(tags))

        
        return (r,g,b)
            
    # Network Measures
    
    def calculatePageRank(self, graph_name):
        graph = nx.read_gexf(f"./{graph_name}.gexf")
        pagerank_scores = nx.pagerank(graph, alpha=0.85)
        
        counts, bins, patches = plt.hist(pagerank_scores.values(), bins=20, color='skyblue', edgecolor='black')
        plt.bar_label(patches, padding=3)

        plt.title('User Network Pagerank Score Distribution')
        plt.xlabel('PageRank Score')
        plt.ylabel('Frequency')
        plt.margins(y=0.1)

        plt.show()
    
    def calculateClosenessCentrality(self, graph_name):
        graph = nx.read_gexf(f"./{graph_name}.gexf")
        closeness = nx.closeness_centrality(graph)
        print(f"harmonic diameter: {nx.harmonic_diameter(graph)}")
        
        counts, bins, patches = plt.hist(closeness.values(), bins=50, color='green', edgecolor='black')

        plt.title('User Network Closeness Centrality Distribution')
        plt.xlabel('Closeness Centrality')
        plt.ylabel('Frequency')

        plt.show()
    
    def calculateClusteringCoefficient(self, graph_name):
        try:
            graph = nx.read_gexf(f"./{graph_name}.gexf")
            ev_centrality = nx.clustering(graph)
            
            counts, bins, patches = plt.hist(ev_centrality.values(), bins=50, color='orange', edgecolor='black')

            plt.title('Clustering Coefficient Distribution')
            plt.xlabel('Clustering Coefficient')
            plt.ylabel('Frequency')

            plt.show()
        except FileNotFoundError:
            print("Could not find a graph to use. Create the graph first.")

    def calculateLocalAvgRelations(self, graph_name):
        try:
            graph = nx.read_gexf(f"./{graph_name}.gexf")
            
            scores = []
            for node in graph.nodes():
                neighbors = graph.neighbors(node)
                score = (graph.degree(node) + sum(graph.degree(neighbor) for neighbor in neighbors)) / (graph.degree(node) + 1)
                scores.append(score)

            counts, bins, patches = plt.hist(scores, bins=50, color='purple', edgecolor='black')
            
            plt.title('Average Number of Relations at Local Level per Node')
            plt.xlabel('Average Relations')
            plt.ylabel('Frequency')

            plt.show()
        except FileNotFoundError:
            print("Could not find a graph to use. Create the graph first.")
        except FileNotFoundError:
            print("Could not find a graph to use. Create the graph first.")
    
    def calculateGlobalAvgRelations(self, graph_name):
        try:
            graph = nx.read_gexf(f"./{graph_name}.gexf")
            return 2 * graph.number_of_edges() / graph.number_of_nodes()
        except FileNotFoundError:
            print("Could not find a graph to use. Create the graph first.")


    def generateWordCloud(self):
        fire_mask = np.array(Image.open("fire_outline.jpg"))
        text =  open('llm_keywords.txt').read()
        
        wc = WordCloud(background_color="white", mask=fire_mask, max_words=3000,scale=3, colormap="jet", stopwords=set(STOPWORDS))
        
        wc.generate(text)

        wc.to_file("wordcloud.png")
            