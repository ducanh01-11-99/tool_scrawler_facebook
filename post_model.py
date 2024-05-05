class Post:
    def __init__(self):
        self.id = ""
        self.type = ""
        self.time_crawl = ""
        self.link = ""
        self.author = ""
        self.author_link = ""
        self.content = ""
        self.created_time = ""
        self.comment = 0
        self.like = 0
        self.haha = 0
        self.wow = 0
        self.sad = 0
        self.love = 0
        self.care = 0
        self.angry = 0
        self.share = 0
        self.avatar = ""
        self.image_url = []
        self.video = []
        self.domain = "https://www.facebook.com"
        self.source_id = ""
        self.hashtag = []

    def is_valid(self) -> bool:
        is_valid = self.id != "" and self.author != "" and self.link != "" and self.created_time 
        return is_valid

    def __str__(self) -> str:
        string = ""
        for attr_name, attr_value in self.__dict__.items():
            string =  f"{attr_name}={attr_value}\n" + string
        return string