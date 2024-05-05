from abc import ABC, abstractmethod
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from post_model import Post
from datetime import datetime


class PostExtractor(ABC):
    post_element: WebElement
    driver: WebDriver

    def __init__(self, post_element: WebElement, driver: WebDriver, source_id="", type=""):
        self.post_element = post_element
        self.driver = driver       
        self.source_id = source_id
        self.type = type

    @abstractmethod
    def extract_post_author(self):
        pass

    # @abstractmethod
    # def extract_post_author_link(self):
    #     pass

    # @abstractmethod
    # def extract_post_author_avatar_link(self):
    #     pass

    @abstractmethod
    def extract_post_time(self):
        pass

    @abstractmethod
    def extract_post_content(self):
        pass


    @abstractmethod
    def extract_post_link(self):
        pass

    @abstractmethod
    def extract_post_id(self):
        pass

    @abstractmethod
    def extract_post_photos(self):
        pass

    @abstractmethod
    def extract_post_comments(self):
        pass
    
    @abstractmethod
    def extract_post_reactions(self):
        pass
    @abstractmethod
    def extract_post_comment(self):
        pass

    @abstractmethod
    def extract_post_share(self):
        pass


    def extract(self) -> Post:
        post = Post()
        author, author_link, author_avatar_link = self.extract_post_author()
        # author_link = self.extract_post_author_link()
        # author_avatar_link = self.extract_post_author_avatar_link()
        created_time = self.extract_post_time()
        content, hashtag = self.extract_post_content()
        link = self.extract_post_link()
        id = self.extract_post_id()
        image_links, video_links = self.extract_post_photos()           
        # like, haha, wow, sad, love, care, angry = self.extract_post_reactions()
        reactions = self.extract_post_reactions()
        num_of_comment  = self.extract_post_comment()
        num_of_share = self.extract_post_share()
        comments = self.extract_post_comments()
        post.time_crawl = datetime.now()
        post.id = id
        post.author = author
        post.author_link = author_link
        post.avatar = author_avatar_link
        post.created_time = created_time
        post.content = content
        post.hashtag = hashtag
        post.link = link
        post.image_url = image_links
        post.video = video_links
        post.comment = num_of_comment
        post.share = num_of_share
        # post.like = like
        # post.haha = haha
        # post.wow = wow
        # post.sad = sad
        # post.love = love
        # post.care = care
        # post.angry = angry
        # post.dataInListComments = comments
        post.source_id = self.source_id
        post.type = self.type

        return post     
    
