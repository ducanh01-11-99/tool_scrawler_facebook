import json

class Account:
    def __init__(self, username, password, cookies):
        self.username = username
        self.password = password
        self.cookies = cookies
        self.expires = False
        self.hash = ""
        self.two_fa_code = ""
        self.proxy = None


    def __str__(self):
        return f"username: {self.username}, password: {self.password}, cookies: {self.cookies}"

    def __repr__(self):
        return f"username: {self.username}, password: {self.password}, cookies: {self.cookies}"

    def __eq__(self, other):
        return self.username == other.username and self.password == other.password

    def __hash__(self):
        return hash(self.username) + hash(self.password)

    def has_cookies(self):
        return self.cookies != ""

    def get_cookies(self):
        return self.cookies

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)