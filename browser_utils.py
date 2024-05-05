import json
import os
import scraper


def get_local_post_with_post_id(folder_path):
    try:
        os.mkdir(folder_path)
    except Exception as e:
        pass
        # print("----Exception tao folder item")
    file_idpost_page = folder_path + 'listPostCmt.json'
    if os.path.isfile(file_idpost_page):
        # print("----Tep json chua bai post da ton tai")
        with open(file_idpost_page) as f:
            local_post = json.load(f)
    else:
        return dict()
    return local_post


def check_post_exist_in_json_file(local_post, id, iCmt):
    try:
        iCmtPost = int(local_post[id])
        iMoreCmt = int(iCmt) - int(iCmtPost)
        
        if int(iMoreCmt / int(iCmtPost)) * 100 < 30:
            return True
        else:
            if iMoreCmt > 30:
                return False
    except Exception as e:
        # print("----Exception: check_post_exist_in_json_file: " + str(e))
        return False


def check_page_is_available(brs):
    try:
        source = brs.get_source().decode('utf-8')
        source_scraper = scraper.Scraper(source)
        
        if source_scraper.soup.text.lower().find("isn't available") != -1:
            print("Page nay khong ton tai-----")
            return False
        else:
            return True
    except Exception as ex:
        print("----Exception: check_page_is_available: " + str(ex))


def check_nick_die(brs):
    source = brs.get_source().decode('utf-8')
    source_scraper = scraper.Scraper(source)
    
    if source_scraper.soup.text.lower().find(
            "your account has been disabled") != -1 or source_scraper.soup.text.lower().find(
            "your account has been locked") != -1:
        print("Tai khoan fb crawl da bi khoa-----")
        return False


def get_like_page(brs):
    iLikePage = "0"
    classLikes = brs.driver.find_elements_by_class_name('taijpn5t.cbu4d94t.j83agx80')
    
    for classLike in classLikes:
        if classLike.text.lower().find("people like this") != -1:
            iLikePage = classLike.text.split(" ")[0].replace(",", "")
            return iLikePage
    return iLikePage


def check_login(brs):
    source = brs.get_source().decode('utf-8')
    source_scraper = scraper.Scraper(source)
    tmp1 = source_scraper.soup.text.lower().find("log in") != -1
    tmp2 = source_scraper.soup.text.lower().find("create new account") != -1
    if tmp1 and tmp2:
        return False


def check_temp_block(brs):
    source = brs.get_source().decode('utf-8')
    source_scraper = scraper.Scraper(source)
    if source_scraper.soup.text.lower().find("you’re temporarily blocked") != -1:
        return False
