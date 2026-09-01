from mastadon_api_service import *
from mastodon import Mastodon
import requests
import os
import json
from dotenv import load_dotenv
import os
from mastodon import Mastodon
from keywords import keywords
import networkx as nx

def main():
    mastadon_service = MastadonAPIService()

def crawlKeywords():
    infomation_diffiusion_network = nx.DiGraph()
    
    for keyword in keywords:
        crawlThroughKeyword(keyword)

def crawlThroughKeyword(graph, keyword: str):
    
    searchResult = MastadonAPIService.search(keyword)
    for status in searchResult.statuses:
        if status.id not in graph:
            crawlStatus(graph=graph, status=status)

def crawlStatus(graph, status):
    graph.add_node(status.id, status=status)
    replies = MastadonAPIService.getReplies(status_id=status.id)

    # Handle Replies
    for reply in replies:
        if reply.id not in graph:
            new_status = MastadonAPIService.getStatus(reply.id)
            crawlStatus(graph, new_status)

        graph.add_edge(status.id, reply.id, relationship="reply")
        
    # Hanlde Parent Post
    if status.in_reply_to_id:
        if status.in_reply_to_id not in graph:
            new_status = MastadonAPIService.getStatus(status.in_reply_to_id)
            crawlStatus(graph, new_status)
        
        graph.add_edge(status.in_reply_to_id, status.id, relationship="reply")
    
    # Handle If Reblog
    if status.reblog:
        if status.reblog.id not in graph:
            new_status = MastadonAPIService.getStatus(status.reblog.id)
            crawlStatus(graph, new_status)
        graph.add_edge(status.reblog.id, status.id, type="reblog")


if __name__ == "__main__":
    main()