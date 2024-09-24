import os

def run_daraz_scraper(search_term):
    os.system(f'scrapy crawl darazscraperpw -a search_term="{search_term}"')

if __name__ == "__main__":
    term = input("Enter a search term: ")
    run_daraz_scraper(term)
