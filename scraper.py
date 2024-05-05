from bs4 import BeautifulSoup


class Scraper:
    def __init__(self, html):
        self.html = html
        self.soup = BeautifulSoup(html, "lxml")
        

    def find_posts(self):
        posts = self.soup.find_all("a")
        print(f'Found {len(posts)} posts.')
        for post in posts:
            print(post)
