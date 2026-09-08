from Crawler import Crawler
from seeds import keywords, seed_users
import json

def main():
    crawler = Crawler()
    crawler.crawlUsers(seedUsers=seed_users)
    # with open("seed_users.json", "r") as file:
    #     users = json.loads(json.load(file))
    #     for key, value in users.items():
    #         print(f"\"{key}\" : \"{value}\",")

if __name__ == "__main__":
    main()
    
