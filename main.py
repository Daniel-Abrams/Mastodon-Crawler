from Crawler import Crawler
from seeds import keywords, seed_users


def main():
    crawler = Crawler()
    crawler.crawlKeywords(keywords=keywords)

if __name__ == "__main__":
    main()