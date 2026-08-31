from mastadon_api_service import *
from mastodon import Mastodon
import requests
import os
import json
from dotenv import load_dotenv
import os
from mastodon import Mastodon
from keywords import keywords

def main():
    mastadon_service = MastadonAPIService()

def crawlKeywords():
    
    for keyword in keywords:
        crawlThroughKeyword(keyword)
        
def crawlThroughKeyword(keyword: str):
    
    searchResult = MastadonAPIService.s


if __name__ == "__main__":
    main()