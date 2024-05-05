import json
from utils import browser, scraper
from selenium.webdriver.common.by import By
import time
import userModel 
path_dir_chdriver = "/usr/bin/chromedriver"

def read_acc_cookies():
    with open('dict_cookies.json', 'r') as fp:
        dict_cookies_open = json.load(fp)
    return dict_cookies_open

def login_fb(self):
        self.brs = None
        self.brs = browser.Browser(path_dir_chdriver)
        self.brs.get_url()

        result = self.brs.loginFacebookByCookie(self.cookie)
        if result == 0:
            return 0


        return 1

"""
HoangLM: check xem page có tồn tại không
Đầu vào: Browser hiện tại
Đầu ra: True, False 
"""
def check_url_isavailable(brs):
    source = brs.get_source().decode('utf-8')
    source_scraper = scraper.Scraper(source)
    if source_scraper.soup.text.lower().find("isn't available") != -1 :
        print("Page nay khong ton tai-----")
        return False
    return True

brs = browser.Browser(path_dir_chdriver)
brs.get_url()
time.sleep(3)
dict_cookies = read_acc_cookies()
cookie = "".join(dict_cookies[2].values())
cookie = cookie.split(":")[1]
brs.loginFacebookByCookie(cookie)
time.sleep(3)


"""
HoangLM:
class này bao gồm các hàm thu thập thông tin của nguời dùng theo id 
"""
class UserInfor: 
    def __init__(self, id):
        self.user_infor = userModel.User()
        self.id = id
    
    """
    HoangLM:
    input: id của người dùng
    output: danh sách các ảnh thu được của người dùng theo id
    """
    def get_image_user_by_id (self):
        url = f'https://www.facebook.com/profile.php?id={self.id}&sk=photos'
        brs.go_url(url, 1)
        time.sleep(3)

        #HoangLM: Tìm đến class chứa các ảnh
        soup = brs.driver.find_element("xpath", "//div[@class='x1e56ztr']")
        html = soup.get_attribute('innerHTML')
        elementPhoto= scraper.Scraper(html).soup
        elementPhoto = elementPhoto.contents[0].contents[0].contents[0].contents
        
        i = 0
        j = 0 # HoangLM: Biến này để đếm chu kỳ scroll page. Mỗi lần scroll sẽ load thêm được 24 ảnh
        while(True):
            try:
                if i < 24:
                    photo = elementPhoto[i]
                    link_Post_Photo = photo.find("a")['href'] # HoangLM: danh sách đường dẫn đến các Post chứa ảnh
                    link_Photo = photo.find("img")['src']  # HoangLM: danh sách đường dẫn các ảnh
                    i += 1 
                else:
                    # Lấy được 24 ảnh thì kéo để hiện thị thêm
                    if j%23 == 0:
                        brs.scroll_page(1)

                        #HoangLM: Tìm đến class chứa các ảnh (cập nhật html của trang)
                        soup = brs.driver.find_element("xpath", "//div[@class='x1e56ztr']")
                        html = soup.get_attribute('innerHTML')
                        elementPhoto= scraper.Scraper(html).soup
                        elementPhoto = elementPhoto.contents[0].contents[0].contents[0].contents
                    photo = elementPhoto[i]
                    link_Post_Photo = photo.find("a")['href'] # HoangLM: danh sách đường dẫn đến các Post chứa ảnh
                    link_Photo = photo.find("img")['src']  # HoangLM: danh sách đường dẫn các ảnh
                    i = i + 1
                    j = j + 1

                self.user_infor.list_src_photo.append(link_Photo)   
                self.user_infor.list_Link_Post_Photo.append(link_Post_Photo)
            except Exception as e:
                print("loi: ", e)
                break

        return self.user_infor.list_Link_Post_Photo, self.user_infor.list_src_photo

    """
    HoangLM:
    input: id user 
    output: number friend of user 
    """
    def get_num_friend_by_id(self):
        # url = 'https://www.facebook.com/profile.php?id=100079028075513'
        url = f'https://www.facebook.com/profile.php?id={self.id}'
        brs.go_url(url, 1)
        time.sleep(3)

        try:
            soup = brs.driver.find_element("xpath", f"//a[@href='https://www.facebook.com/profile.php?id={self.id}&sk=friends']")
            html = soup.get_attribute('innerHTML')
            self.user_infor.num_friend = html.split('<!-- -->')[0] # html format [<num_friend> <!-- --> friends]
            if "K" in self.user_infor.num_friend: # eg: 2.8K friends
                self.user_infor.num_friend = int(float(self.user_infor.num_friend[:-1])*1000)
        except:
            self.user_infor.num_friend = 0
            print("don't public friend list or error url")
        return self.user_infor.num_friend

    """
    HoangLM:
    input: id của user
    output: danh sách bạn bè của user đó
    """
    def get_list_friend_user_by_id(self):

        numFriend = self.get_num_friend_by_id()
        url = f'https://www.facebook.com/profile.php?id={self.id}&sk=friends'
        brs.go_url(url, 1)
        time.sleep(3)

        #HoangLM: Tìm đến class chứa bạn bè
        soup = brs.driver.find_element("xpath", "//div[@class='x78zum5 x1q0g3np x1a02dak x1qughib']")
        html = soup.get_attribute('innerHTML')
        elementFriend= scraper.Scraper(html).soup
        elementFriend = elementFriend.contents[1]
        elementFriend = elementFriend.contents[0]
        i = 0
        j = 0 # HoangLM: Biến này để đếm chu kỳ scroll page. Mỗi lần scroll sẽ load thêm được 8 bạn bè
        while(i < numFriend):  
            # HoangLM: tạm: chạy đến khi nào lỗi thì không lấy link bạn bè nữa 
            try:          
                if i < 24:
                    element = elementFriend.contents[i]
                    i = i+3
                    friend_link = element.find("a")['href']
                else:
                    element = elementFriend.contents[i]
                    i = i+1
                    friend_link = element.find("a")['href']
                    # lấy được 8 bạn bè thì kéo để hiển thị thêm
                    if(j%7==0):
                        brs.scroll_page(1)
                        soup = brs.driver.find_element("xpath", "//div[@class='x78zum5 x1q0g3np x1a02dak x1qughib']")
                        html = soup.get_attribute('innerHTML')
                        elementFriend= scraper.Scraper(html).soup
                        elementFriend = elementFriend.contents[1]
                        elementFriend = elementFriend.contents[0]
                    j = j + 1
            
                self.user_infor.listFriend.append(friend_link)
            except Exception as e:
                print("loi: ", e)
                break
        return self.user_infor.listFriend


user_infor = UserInfor(100058764403790)
# a, b = user_infor.get_image_user_by_id()
# a = user_infor.get_num_friend_by_id()
a = user_infor.get_list_friend_user_by_id()
print(a)
print('ok')