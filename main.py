from Crawler import Crawler
from keywords import keywords


def main():
    crawler = Crawler()
    crawler.crawlKeywords(keywords=keywords)    

if __name__ == "__main__":
    main()