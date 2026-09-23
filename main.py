import argparse

from Crawler import Crawler
from Grapher import Grapher
from seeds import keywords, seed_users

from mastodon_api_service import MastodonAPIService

def main():
    parser = argparse.ArgumentParser(prog='main')
    parser.add_argument("mode", choices=['get-access-token','crawl-keywords','crawl-users','info-graph','user-graph','network-measures', 'generate-wordcloud'])

    
    args = parser.parse_args()
    
    match args.mode:
        case 'get-access-token':
            mastodonAPIService = MastodonAPIService()
            mastodonAPIService.getAccessToken()
        case 'crawl-keywords':
            crawler = Crawler()
            crawler.crawlKeywords(keywords=keywords)
        case 'crawl-users':
            crawler = Crawler()
            crawler.GetRelevantUsers(seedUsers=seed_users)
        case 'info-graph':
            grapher = Grapher()
            grapher.constructInfoDiffusionNetwork()
        case 'user-graph':
            grapher = Grapher()
            grapher.constructUserGraph()
        case 'network-measures':
            grapher = Grapher()
            print(f"Local avg relations of user network: {grapher.calculateLocalAvgRelations('user_network_LAFires')}")
            print(f"Global avg relations of user network: {grapher.calculateGlobalAvgRelations('user_network_LAFires')}")
            grapher.calculatePageRank('user_network_LAFires')
            grapher.calculateClusteringCoefficient('user_network_LAFires')
            grapher.calculateClosenessCentrality('user_network_LAFires')
        case 'generate-wordcloud':
            grapher = Grapher()
            grapher.generateWordCloud()

    # with open("seed_users.json", "r") as file
    

if __name__ == "__main__":


    main()
    
