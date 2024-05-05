import base64
import json
import time
import config
import pickle
import scraper
import traceback
from post_model import Post
from utils import utils
# from kafka import KafkaProducer
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from browser import WebBrowser
from browser_utils import get_local_post_with_post_id, \
    check_post_exist_in_json_file, \
    check_login, \
    check_nick_die, \
    check_temp_block

#producer = KafkaProducer(bootstrap_servers=[config.kafka_address])




def get_list_post_from_account(brs):
    try:
        lstIdSectionPost = []
        size_post = 0
        iDem = 0
        status_crawl = 0

        while (1):
            check_state_account_fb(iDem=iDem, brs=brs)
            scroll_page(account_brower=brs)
            artical_posts = get_list_post_use_tag_selenium(brs=brs)
            status_crawl = check_number_post_scrolled(artical_posts=artical_posts, size_post=size_post)
            size_post = len(artical_posts)
            for id in range(len(artical_posts)):
                is_id_exist = False
                # print("-Dang xu li bai post thu ", id + 1)
                lstIdSectionPost, iDem, is_id_exist = get_post_from_account_and_push_kafka(artical_posts=artical_posts,
                                                                                           id=id,
                                                                                           brs=brs,
                                                                                           lstIdSectionPost=lstIdSectionPost,
                                                                                           iDem=iDem,
                                                                                           is_id_exist=is_id_exist)
                if is_id_exist:
                    # print("--Bai post nay da duoc lay trong cung 1 phien dang nhap")
                    continue
            if status_crawl == config.crawl_complete_one_run:
                break
    except Exception as exc:
        print("----Exception: get_list_post_from_account: " + str(exc))
        return config.crawl_re_login
    return status_crawl


def check_state_account_fb(iDem, brs):
    if iDem > 200:
        print("----Da lay qua 200 bai")
    if check_login(brs)==False:
        print("----Nick khong dang nhap duoc")
        return 3
    elif  check_nick_die(brs) ==False:
        print("----Nick bi chan hoac khoa")
        return 2
    elif  check_temp_block(brs) ==False:
        print("----Nick bi khoa chuc nang tam thoi")
        return 5


def scroll_page(account_brower):
    account_brower.scroll_page(config.number_page)
    # chờ để tránh facebook phát hiện bot
    time.sleep(config.time_wait_after_scroll_page)


def get_list_post_use_tag_selenium(brs):
    artical_posts = brs.driver.find_elements("xpath", "//div[@aria-posinset]")
    print("So bai post hien thi tren giao dien: " + str(len(artical_posts)))
    return artical_posts


def check_number_post_scrolled(artical_posts, size_post):
    if len(artical_posts) == size_post:
        print("----Khong lay duoc them bai moi tren giao dien")
        return config.crawl_complete_one_run
    if len(artical_posts) <= 1:
        print("----Chi co <= 1 bai tren giao dien")
        return config.crawl_complete_one_run
    return config.crawl_continue


def get_post_from_account_and_push_kafka(artical_posts, id, brs, lstIdSectionPost, iDem, is_id_exist):
    try:
        posts = []
        comments = []
        postElement = Post()
        element_account_old_or_new = 0
        artical = artical_posts[id]

        if artical.id in lstIdSectionPost:
            is_id_exist = True
            return lstIdSectionPost, iDem, is_id_exist
        else:
            lstIdSectionPost.append(artical.id)

        artical.location_once_scrolled_into_view
        soup, element_account_old_or_new = check_account_old_or_new(artical=artical,
                                                                    element_account_old_or_new=element_account_old_or_new)
        soup = show_all_info_of_post(soup=soup, artical=artical, brs=brs,
                                     element_account_old_or_new=element_account_old_or_new)
        get_time_of_post(soup=soup, artical=artical, element_account_old_or_new=element_account_old_or_new,
                         postElement=postElement)

        if get_all_info_of_post(soup, postElement, comments, element_account_old_or_new):
            if postElement._id != "":
                posts.append(postElement)
                iDem += 1
                push_kafka_value = push_kafka(posts, comments)
                if push_kafka_value == config.push_kafka_sucess:
                    print("----Da lay xong bai viet tai khoan: ", postElement.author)
    except Exception as exc:
        print("----Exception: get_post_from_account_and_push_kafka: " + str(exc))
    return lstIdSectionPost, iDem, is_id_exist


def check_account_old_or_new(artical, element_account_old_or_new):
    soup = get_soup_element(artical.get_attribute('innerHTML'))
    sub_soup = soup.contents[0].contents[0].contents[0].contents[0].contents[0].contents[0].contents[0].contents
    # kich thuoc nho hon 3 la tai khoan moi tao
    if (len(sub_soup) > 2):
        element_account_old_or_new = config.element_account_old
    else:
        element_account_old_or_new = config.element_account_new

    return soup, element_account_old_or_new


def get_soup_element(source):
    source_scraper = scraper.Scraper(source)
    return source_scraper.soup


def show_all_info_of_post(soup, artical, brs, element_account_old_or_new):
    click_seemore_and_show_comment(brs, artical, soup, element_account_old_or_new)
    soup = get_soup_element(artical.get_attribute('innerHTML'))
    click_view_more_comment(brs, artical, soup, element_account_old_or_new)
    soup = get_soup_element(artical.get_attribute('innerHTML'))

    return soup


def click_seemore_and_show_comment(brs, artical, soup, element_account_old_or_new):
    try:
        contents_structs = goto_element_contain_content_common_of_html_post(soup, element_account_old_or_new)
        struct_infor_post = contents_structs[2]
        click_all_see_more(brs, artical, struct_infor_post)
        struct_infor_cmt = contents_structs[len(contents_structs) - 1]
        click_show_comments(brs, artical, struct_infor_cmt)
    except Exception as e:
        print("----Exception click_seemore_and_show_comment", e)


def click_all_see_more(brs, artical, struct_infor_post):
    try:
        struct_infor = struct_infor_post.contents[0].contents[0].contents[0].contents[0].contents
        for infor_content in struct_infor:
            try:
                if infor_content.text.lower().find("see more") != -1:
                    struct_see_mores = infor_content.contents
                    for struct_see_more in struct_see_mores:
                        try:
                            if struct_see_more.text.lower().find("see more") != -1:
                                tagButton = struct_see_more.contents
                                if len(tagButton) > 1:
                                    if "class" not in tagButton[len(tagButton) - 1].attrs:
                                        class_div = ".".join(tagButton[len(tagButton) - 1].find("div").attrs["class"])
                                    else:
                                        class_div = ".".join(tagButton[len(tagButton) - 1].attrs["class"])
                                elif len(tagButton) == 1:
                                    if "class" not in tagButton[0].contents[len(tagButton[0]) - 1].attrs:
                                        class_div = ".".join(
                                            tagButton[0].contents[len(tagButton[0]) - 1].find("div").attrs["class"])
                                    else:
                                        class_div = ".".join(
                                            tagButton[0].contents[len(tagButton[0]) - 1].attrs["class"])
                                elements_see = artical.find_elements_by_class_name(class_div)
                                for element in elements_see:
                                    if element.text.lower().find("see more") != -1:
                                        try:
                                            brs.driver.execute_script("arguments[0].click();", element)
                                            time.sleep(config.time_wait_after_interactive_post)
                                            # print("----click See more done")
                                        except Exception as e:
                                            print("----Exception click See more", e)
                        except Exception as e:
                            print("----Exception struct_see_more.text in click_all_see_more ", e)
            except Exception as e:
                print("----Exception infor_content.text in click_all_see_more ", e)
    except Exception as e:
        print("----Exception click_all_see_more", e)


def click_show_comments(brs, artical, struct_infor_cmt):
    try:
        struct_infor = struct_infor_cmt.contents[0].contents
        for struct_cmt_infor in struct_infor:
            try:
                struct_infor_cmts = struct_cmt_infor.contents[0].contents[0].contents[0].contents[0].contents
                for struct_cmt_share in struct_infor_cmts:
                    try:
                        if struct_cmt_share.text.find("Comment") != -1:
                            for struct_cmt in struct_cmt_share.contents:
                                if struct_cmt.text.find("Comment") != -1:
                                    class_comments = ".".join(
                                        struct_cmt.contents[0].attrs["class"])
                                    elements_comments = artical.find_elements_by_class_name(
                                        class_comments)
                                    for element in elements_comments:
                                        if element.text.find("Comment") != -1:
                                            try:
                                                brs.driver.execute_script("arguments[0].click();", element)
                                                # element.send_keys("\n")
                                                time.sleep(config.time_wait_after_interactive_post)
                                                # print("----click show comments done")
                                                return
                                            except Exception as e:
                                                print("----Exception click show comments", e)
                    except Exception as e:
                        print("----Exception struct_cmt_share.text in click_show_comments", e)
            except Exception as e:
                print("----Exception struct_cmt_infor click_show_comments", e)
    except Exception as e:
        print("----Exception click_show_comments", e)


def check_title_diff(contents_structs):
    if len(contents_structs) > 4:
        struct_infor_cmt = contents_structs[4]
    else:
        struct_infor_cmt = contents_structs[3]
    return struct_infor_cmt


def click_view_more_comment(brs, artical, soup, element_account_old_or_new):
    try:
        contents_structs = goto_element_contain_content_common_of_html_post(soup=soup,
                                                                            element_account_old_or_new=element_account_old_or_new)
        struct_infor_cmt = check_title_diff(contents_structs=contents_structs)
        click_view_more_cmt(brs, artical, struct_infor_cmt)
    except Exception as e:
        print("----Exception click_view_more_comment", e)


def click_view_more_cmt(brs, artical, struct_infor_cmt):
    try:
        struct_infor = struct_infor_cmt.contents[0].contents
        for struct_cmt_infor in struct_infor:
            try:
                for struct_cmt_sha in struct_cmt_infor.contents:
                    struct_infor_cmts = struct_cmt_sha.contents
                    for struct_cmt_share in struct_infor_cmts:
                        if struct_cmt_share.text.find("more comment") != -1 or struct_cmt_share.text.find(
                                "iew comment") != -1:
                            struct_cmts = struct_cmt_share.contents
                            for struct_cmt in struct_cmts:
                                for struct_view in struct_cmt.contents:
                                    if struct_view.text.find("more comment") != -1 or struct_view.text.find(
                                            "iew comment") != -1:
                                        class_comments = ".".join(struct_view.attrs["class"])
                                        elements_comments = artical.find_elements_by_class_name(class_comments)
                                        for element in elements_comments:
                                            if element.text.find("more comment") != -1 or element.text.find(
                                                    "iew comment") != -1:
                                                try:
                                                    brs.driver.execute_script("arguments[0].click();", element)
                                                    time.sleep(config.time_wait_after_interactive_post)
                                                    # print("----Click view more comment done")
                                                    return
                                                except Exception as e:
                                                    print(
                                                        "----Exception khi click view more comment click_view_more_cmt",
                                                        e)
            except Exception as e:
                print("----Exception struct_cmt_infor click_view_more_cmt", e)
    except Exception as e:
        print("----Exception click_view_more_cmt", e)


def get_time_of_post(soup, artical, element_account_old_or_new, postElement):
    soup, text_time = mouser_click(artical, soup, element_account_old_or_new)
    postElement.created_time, distance_time = utils.get_create_time(text_time)


def mouser_click(artical, soup, element_account_old_or_new):
    contents_structs = goto_element_contain_content_common_of_html_post(soup=soup,
                                                                        element_account_old_or_new=element_account_old_or_new)

    for struct_time in contents_structs[1].contents[0].contents[1].contents[0].contents[1].contents[0].contents[
        0].contents:
        if "class" not in struct_time.attrs:
            id_post_kol = struct_time.contents[0].contents[0]
    class_name = ".".join(id_post_kol.attrs["class"])
    artical.location_once_scrolled_into_view
    ele_button = artical.find_element(By.CLASS_NAME, class_name)
    ele_button.send_keys(Keys.PAGE_UP)
    time.sleep(config.time_wait_after_interactive_post)

    return get_soup_element(artical.get_attribute('innerHTML')), get_text_time(ele_button)


def get_text_time(ele_button):
    arr_texts = []

    struct_time = get_soup_element(ele_button.get_attribute('innerHTML'))
    struct_text = struct_time.contents[0].contents[0].contents[0].contents[0]
    if str(type(struct_text)).find("String") != -1:
        return str(struct_text)
    first_text = struct_text.contents[len(struct_text.contents) - 1].contents[0]
    if str(type(first_text)).find("String") != -1:
        arr_texts.append(first_text)
    all_span_text = struct_text.contents[len(struct_text.contents) - 1].find_all("span")
    if len(all_span_text) == 0:
        all_span_text = struct_text.contents[len(struct_text.contents) - 1].find_all("b")
    for span_text in all_span_text:
        if "style" not in span_text.attrs:
            arr_texts.append(span_text.text)

    return "".join(arr_texts).replace("\xa0", " ")


def get_all_info_of_post(soup, postElement, comments, element_account_old_or_new):
    try:
        contents_structs = goto_element_contain_content_common_of_html_post(soup=soup,
                                                                            element_account_old_or_new=element_account_old_or_new)
        # HoangLM: thông tin user post
        struct_infor_user = contents_structs[1]
        get_info_kol_post(struct_infor_user, postElement)
        struct_infor_post = contents_structs[2]
        get_info_content_post(struct_infor_post, postElement)
        struct_infor_count = check_title_diff(contents_structs=contents_structs)
        # HoangLM: thông tin like cmt share
        get_count_comment_like_share(struct_infor_count, postElement)
        id_post = postElement._id.split("_")[-1]
        folder_path = "listPostCmt_search/" + postElement._id.split("_")[0] + "/"
        local_post = get_local_post_with_post_id(folder_path)
        if check_post_exist_in_json_file(local_post, id_post, postElement.comment) == False:
            get_comment_in_post(struct_infor_count, postElement, comments)
            local_post[id_post] = postElement.comment
            update_post_to_json(folder_path, local_post)
        else:
            print("----get_all_info_of_post: Bai post nay da duoc quet, khong qua luat check scaned post")
            return False
    except Exception as e:
        print("----Exception: get_all_info_of_post: " + str(e))
        return True

    return True


def get_info_kol_post(struct_infor_user, postElement):
    try:
        # lấy ra link avt image, link bài post
        struct_link_avatar = struct_infor_user.contents[0].contents[0]
        link_avt = struct_link_avatar.find("image")["xlink:href"]
        link_post = struct_infor_user.contents[0].contents[1].contents[0].contents[1].find_all('a', href=lambda href: href and 'https://www.facebook.com' in href)[0]['href']
        # lấy ra tên và link facebook KOL
        user_fb_kol = struct_infor_user.contents[0].contents[1]
        author_link = user_fb_kol.contents[0].contents[0].contents[0].contents[0].find("a").attrs["href"]
        author_link = author_link.split("?")[0]
        # HoangLM: lay ten cua tac gia bai viet
        author = user_fb_kol.contents[0].contents[0].contents[0].contents[0].find("a").text
        postElement.link = link_post
        postElement.author = author
        postElement.avatar = link_avt
        if postElement.link.find("group") != -1:
            if author_link.find("/user/") != -1:
                author_link = postElement.domain + "/" + author_link.split("/user/")[-1].replace("/", "")
            postElement.author_link = author_link
            postElement._id = link_post.split("/groups/")[1].replace("/posts/", "_").replace("/", "")
            postElement.type_id = 3
            postElement.type = "facebook group"
        else:
            postElement.author_link = author_link
            postElement._id = author_link.split(".com")[-1].replace("/", "") + "_" + link_post.split("/")[-1]
            postElement.type_id = 1
            postElement.type = "facebook page"
    except Exception as e:
        print("----Exception get_info_kol_post", e)

    return


def get_info_content_post(struct_infor_post, postElement):
    contents = []
    url = set()

    try:
        # HoangLM: lấy nội dung bài viết
        struct_posts = struct_infor_post.contents[0].contents[0].contents[0].contents[0].contents
        for infor_content in struct_posts:
            contents.append(infor_content.text)
        # lấy link ảnh và video, url
        if len(struct_infor_post.contents) > 1:
            all_image = struct_infor_post.find_all("img")
            for image in all_image:
                url_img = image["src"]
                if url_img.find("facebook.com") == -1:
                    url.add(url_img)
    except Exception as e:
        print("----Exception get_info_content_post", e)
    content = " ".join(contents)
    postElement.content = content
    postElement.content_length = len(postElement.content)
    postElement.image_url = list(url)

    return


def get_count_comment_like_share(struct_infor_count, postElement):
    iLike = 0
    iCmt = 0
    iShare = 0
    try:
        struct_infor_cmt_share = struct_infor_count.contents[0].contents
        for infor_content in struct_infor_cmt_share:
            try:
                if infor_content.text.find("Comment") != -1:
                    content_cmt_share = infor_content.contents[0].contents[0].contents[0].contents[0].contents
                    for count_infor in content_cmt_share:
                        if count_infor.text.find("Comment") != -1 or count_infor.text.find("Share") != -1:
                            for count_cmt_sh in count_infor.contents:
                                # Comment
                                if count_cmt_sh.text.find("Comment") != -1:
                                    iCmt = get_count_comment(count_cmt_sh=count_cmt_sh)
                                # Share
                                elif count_cmt_sh.text.find("Share") != -1:
                                    iShare = get_count_share(count_cmt_sh=count_cmt_sh)
                        elif count_infor.text != "":
                            iLike = get_count_like(count_infor=count_infor)
            except Exception as e:
                print("----Exception infor_content.text in get_count_comment_like_share", e)
    except Exception as e:
        print("----Exception get_count_comment_like_share", e)
    write_count_like_share_comment_to_post_model(iLike=iLike, iShare=iShare, iCmt=iCmt, postElement=postElement)
    return


def get_count_comment(count_cmt_sh):
    iCmt = count_cmt_sh.text.split(" ")[0]
    if iCmt.find("K") != -1:
        sKCount = iCmt.replace("K", "")
        iCmt = int(float(sKCount) * 1000)
    return iCmt


def get_count_share(count_cmt_sh):
    iShare = count_cmt_sh.text.split(" ")[0]
    if iShare.find("K") != -1:
        sKCount = iShare.replace("K", "")
        iShare = int(float(sKCount) * 1000)
    return iShare


def get_count_like(count_infor):
    iLike = count_infor.text.split(" ")[0]
    if iLike == 'All':
        iLike = count_infor.find("span", {"class": "xrbpyxo x6ikm8r x10wlt62 xlyipyv x1exxlbk"}) \
            .find("span", {"class": "xt0b8zv x1e558r4"}).text
    if iLike.find("K") != -1:
        sKCount = iLike.replace("K", "")
        iLike = int(float(sKCount) * 1000)
    return iLike


def write_count_like_share_comment_to_post_model(iLike, iCmt, iShare, postElement):
    write_count_like_to_post_model(iLike=iLike, postElement=postElement)
    write_count_comment_to_post_model(iCmt=iCmt, postElement=postElement)
    write_count_share_to_post_model(iShare=iShare, postElement=postElement)
    postElement.Interactive = postElement.comment + postElement.like + postElement.share
    postElement.spread = postElement.Interactive

    return


def write_count_like_to_post_model(iLike, postElement):
    try:
        if iLike == "":
            postElement.like = 0
        else:
            postElement.like = int(iLike)
    except Exception as e:
        print("----Exception write_count_like_to_post_model", e)


def write_count_share_to_post_model(iShare, postElement):
    try:
        if iShare == "":
            postElement.share = 0
        else:
            postElement.share = int(iShare)
    except Exception as e:
        print("----Exception write_count_share_to_post_model", e)


def write_count_comment_to_post_model(iCmt, postElement):
    try:
        if iCmt == "":
            postElement.comment = 0
        else:
            postElement.comment = int(iCmt)
    except Exception as e:
        print("----Exception write_count_comment_to_post_model", e)


def get_comment_in_post(struct_infor_cmt, postElement, comments):
    try:
        postCMT = Post()
        postCMT.source_id = postElement._id
        postCMT._id = postElement._id
        postCMT.type = "facebook comment"
        postCMT.type_id = postElement.type_id + 1
        postCMT.content_post = postElement.content
        for struct_infor in struct_infor_cmt.contents[0].contents:
            if str(type(struct_infor)).find("Tag") == -1:
                continue
            for str_infor in struct_infor.contents:
                try:
                    struct_infor_s = str_infor.contents
                    for struct_cmts in struct_infor_s:
                        try:
                            if struct_cmts.text.find("Reply") != -1:
                                print("----Doc duoc " + str(len(struct_cmts)) + " comments trong bai post")
                                for struct_cmt in struct_cmts:
                                    get_comment_brief(struct_cmt, postElement, comments)
                        except Exception as e:
                            print("----Exception: get_comment_in_post: struct_cmt.text: " + str(e))
                except Exception as e:
                    print("----Exception: get_comment_in_post: struct_infor_s: ", + str(e))
    except Exception as e:
        print("----Exception: get_comment_in_post: " + str(e))


def get_comment_brief(struct_cmt, postElement, comments):
    content_cmt = ""
    link_user_cmt = ""
    name_user_cmt = ""

    for str_infor in struct_cmt.contents:
        if str(type(str_infor)).find("Tag") == -1:
            continue
        for struct_user_cmts in str_infor.contents:
            try:
                if struct_user_cmts.text.find("Like") != -1:
                    for struct_user_cmt in struct_user_cmts.contents:
                        for struct_cmt_child in struct_user_cmt.contents:
                            try:
                                struct_user_cmt_chil_cmt = \
                                struct_cmt_child.contents[0].contents[0].contents[0].contents[0].contents
                                href_link = struct_user_cmt_chil_cmt[0].find("a")["href"]
                                if href_link.find("groups") != -1:
                                    link_user_cmt = href_link.split("__cft__")[0]
                                    if link_user_cmt.find("/user/") != -1:
                                        link_user_cmt = link_user_cmt.split("/user/")[-1].replace("?", "").replace("/",
                                                                                                                   "")
                                    else:
                                        link_user_cmt = link_user_cmt.split("https://www.facebook.com/")[-1]
                                    name_user_cmt = struct_user_cmt_chil_cmt[0].find("a").text
                                    cmt_id = link_user_cmt.split("=")[-1].replace("&", "")
                                    link_user_cmt = "https://www.facebook.com/" + link_user_cmt
                                else:
                                    link_user_cmt = href_link.split("comment_id")[0]
                                    name_user_cmt = struct_user_cmt_chil_cmt[0].find("a").text
                                    cmt_id = struct_user_cmt_chil_cmt[0].find("a")[
                                        "href"].split("comment_id")[1].split("&__cft__")[0].replace("=", "").split("%")[
                                        0]
                                    cmt_id = base64.b64decode(cmt_id + '=' * (-len(cmt_id) % 4)).decode("utf-8")
                                    cmt_id = cmt_id.split("_")[-1]
                                print("link_user_cmt: ", link_user_cmt)
                                # check comment co image
                                if len(struct_user_cmt_chil_cmt) > 1:
                                    content_cmt = struct_user_cmt_chil_cmt[1].text.replace(name_user_cmt, "")
                                else:
                                    content_cmt = struct_user_cmt_chil_cmt[0].text.replace(name_user_cmt, "")
                                try:
                                    link_avt = struct_user_cmts.find("image")["xlink:href"]
                                except:
                                    link_avt = ""
                                try:
                                    text_time = struct_user_cmt.contents[len(
                                        struct_user_cmt.contents) - 1].find("a").text
                                except:
                                    text_time = ""
                                postCMT = create_post_cmt(postElement,
                                                          cmt_id,
                                                          content_cmt,
                                                          name_user_cmt,
                                                          link_user_cmt,
                                                          link_avt,
                                                          text_time)
                                comments.append(postCMT)
                            except Exception as e:
                                print("Exception: struct_cmt_child: " + str(e))
                                continue
            except Exception as e:
                print("----Exception struct_user_cmt.text get_comment_in_post", e)


def create_post_cmt(postElement, cmt_id, content_cmt, name_user_cmt, link_user_cmt, link_avt, text_time):
    postCMT = Post()

    postCMT.source_id = postElement._id
    postCMT._id = postElement._id + "_" + cmt_id
    postCMT.type = "facebook comment"
    postCMT.type_id = postElement.type_id + 1
    postCMT.content_post = postElement.content
    postCMT.content = content_cmt
    postCMT.author = name_user_cmt
    postCMT.link = postCMT.domain + "/" + postCMT._id
    postCMT.author_link = link_user_cmt
    postCMT.avatar = link_avt
    postCMT.content_length = len(postCMT.content)
    postCMT.created_time, distance_time = utils.get_create_time(text_time)

    return postCMT


def update_post_to_json(folder_path, local_post):
    file_idpost_page = folder_path + 'listPostCmt.json'
    try:
        with open(file_idpost_page, "w") as outfile:
            json.dump(local_post, outfile)
            outfile.close()
    except Exception as ex:
        print("----Exception update_post_to_json: " + str(ex))


def push_kafka(posts, comments):
    if len(posts) > 0:
        bytes_obj = pickle.dumps([ob.__dict__ for ob in posts])
        #producer.send('lnmxh', bytes_obj)
        return config.push_kafka_sucess
    else:
        return config.push_kafka_fail

    # if len(comments) > 0:
    #     bytes_obj = pickle.dumps([ob.__dict__ for ob in comments])
    #     producer.send('lnmxh', bytes_obj)


def goto_element_contain_content_common_of_html_post(soup, element_account_old_or_new):
    try:
        soup = soup.contents[0]
        soup = soup.contents[0]
        soup = soup.contents[0]
        soup = soup.contents[0]
        soup = soup.contents[0]
        soup = soup.contents[0]
        soup = soup.contents[0]
        soup = soup.contents[element_account_old_or_new]
        soup = soup.contents[0]
        soup = soup.contents[0]
        contents_structs = soup.contents
        return contents_structs
    except Exception as ex:
        print("----Exception Lay phan tu chua thon tin chung cua the html")


def get_url_attach_keyword(keyword):
    # Kiem tra tu khoa co chua '#' hay khong
    if keyword.find("#") != -1:
        url = config.hasgtag_fb + keyword.replace("#", "")
    else:
        url = config.search_post_fb + keyword + config.filter_post_recent
    return url


def parse_keyword_topic_list(key):
    andWord = []
    orWord = []
    keyword_list = []
    if (key):
        for x in key.split("+"):
            if (len(x.split(',')) > 1):
                for orword in x.split(','):
                    orWord.append(orword.lstrip())
            else:
                andWord.append(x.lstrip())
    for i in andWord:
        for j in orWord:
            keyword_list.append(i + " " + j)
    return keyword_list


if __name__ == '__main__':
    web_browser = WebBrowser()
    visit_url = "/" + "groups/1497469973862055"
    web_browser.driver.get("https://facebook.com" + visit_url)
    get_list_post_from_account(web_browser)