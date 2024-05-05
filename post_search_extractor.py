import time
from typing import Callable, List, Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from post_extractor import PostExtractor
from selenium_utils import SeleniumUtils
from utils.log_utils import logger
from utils.common_utils import CommonUtils
from post_model import Post
import json
from unidecode import unidecode
from selenium.webdriver.common.action_chains import ActionChains
from utils.utils import write_data_to_file, read_data_from_file
import queue
import threading
import re

class PostElementIterator:
    def __init__(self, post_element_list: List[WebElement]):
        self.post_element_list = post_element_list
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index >= len(self.post_element_list):
            raise StopIteration

        post = self.post_element_list[self.index]
        self.index += 1
        return post
    
    def _len(self):
        return len(self.post_element_list)

    def update(self, post_element_list: List[WebElement]):
        self.post_element_list = post_element_list


class LinkPostDesktopSearchExtractor:
    driver: WebDriver
    FACEBOOK_SEARCH_LINK: str = "https://www.facebook.com/search/posts?q="
    RECENT_POST_FILTER: str = "&filters=eyJyZWNlbnRfcG9zdHM6MCI6IntcIm5hbWVcIjpcInJlY2VudF9wb3N0c1wiLFwiYXJnc1wiOlwiXCJ9In0%3D"
    POST_XPATH: str = './/div[@aria-posinset]'
    LINK_POST_XPATH: str = './/a[contains(@class, "xt0b8zv xo1l8bm") and @tabindex and @role="link" and not(contains(@href, "/user/"))]'
    POST_ID_REGEX_PATTERN = r"(\/posts\/|\/videos\/|\/videos\/\?v=|photo\.php\?fbid=|\/permalink.php\?story_fbid=|multi_permalinks=)([a-zA-Z0-9]+)"
    FACEBOOK_BASE_URL: str = "https://www.facebook.com"
    # LINK_POST_XPATH: str = './/a[contains(@class, "xt0b8zv xo1l8bm") and @tabindex and @role="link"]'

    link_posts: List[Post] = []
    callback: Optional[Callable[[Post], None]] = None

    def __init__(self, driver: WebDriver, keyword: str, share_queue: queue.Queue() ,  callback: Optional[Callable[[Post], None]] = None):
        self.url = f"{self.FACEBOOK_SEARCH_LINK}{keyword}{self.RECENT_POST_FILTER}"
        self.callback = callback
        self.driver = driver
        self.actions = ActionChains(driver)
        self.keyword = keyword
        self.q_posts_group = share_queue
        self.queueLock = threading.Lock()

        try:
            self.link_posts_all = read_data_from_file(path_file=f"db/Search/{self.keyword.replace(' ', '_')}.txt")
            self.link_crawl_done = read_data_from_file(f"db/Search/{self.keyword.replace(' ', '_')}_done.txt")
            
            for link_ in self.link_posts_all:
                if link_ not in self.link_crawl_done:
                    if self.q_posts_group.full():
                        logger.warning("Hàng đợi đã đầy")
                        
                        slept_time = CommonUtils.sleep_random_in_range(1000, 2000)
                        logger.debug(f"Slept {slept_time}")
                        
                    else:
                        self.queueLock.acquire()
                        self.q_posts_group.put(link_)
                        self.queueLock.release()
                    self.link_posts.append(link_)
        except:
            logger.warning(f"File not found {self.keyword.replace(' ', '_')}.txt")
            self.link_posts = []

        self.driver.get(self.url)
        self.driver.implicitly_wait(1000)
        self._scroll()
        slept_time = CommonUtils.sleep_random_in_range(1, 5)
        logger.debug(f"Slept {slept_time}")

    def _scroll(self):
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.driver.implicitly_wait(3)
        except Exception as e:
            logger.error(e)

    def _get_elements_by_xpath(self, XPATH_, parent_element: Optional[WebElement] = None):
        try:
            self.driver.implicitly_wait(1)
            if parent_element is not None:
                return parent_element.find_elements(by=By.XPATH, value=XPATH_)
            return self.driver.find_elements(by=By.XPATH, value=XPATH_)
        except NoSuchElementException as e:
            logger.error(f"Not found {XPATH_}")
            return None
        except Exception as e:
            logger.error(e, exc_info=True)
            return None
        
    def _get_element_by_xpath(self, XPATH_, parent_element: Optional[WebElement] = None):
        try:
            self.driver.implicitly_wait(1)
            if parent_element is not None:
                return parent_element.find_element(by=By.XPATH, value=XPATH_)
            return self.driver.find_element(by=By.XPATH, value=XPATH_)
        except NoSuchElementException as e:
            logger.error(f"Not found {XPATH_}")
            return None
        except Exception as e:
            logger.error(e, exc_info=True)
            return None
        
        
    def start_get_link_posts(self):
        logger.info("get link posts")
        post_element_list = self._get_elements_by_xpath(self.POST_XPATH)
        post_element_iterator = PostElementIterator(post_element_list=post_element_list)
        iDem = 0
        #hàm lấy link bài viết từ các post element
        def _get_link_from_post_element(element):
            #############
            element_link = self._get_element_by_xpath(self.LINK_POST_XPATH, element)
            if element_link:
                # reel ko có link này 
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element_link)
            #element_link.click()
                self.actions.move_to_element(element_link).perform()
                CommonUtils.sleep_random_in_range(1,4)
                element_link = self._get_element_by_xpath(self.LINK_POST_XPATH, element)
                link_post = element_link.get_attribute("href")
            ## check xem bài viết quá time hay chưa
           
            return link_post
        
        id_element = 0
        
        check_out = True
        while check_out:
            try:
                element = next(post_element_iterator)
                id_element = post_element_iterator.index
                link_post = _get_link_from_post_element(element=element)
                
                if "/groups/" in link_post:
                    match = re.search(pattern=self.POST_ID_REGEX_PATTERN, string=link_post)
                    if match:
                        post_id = match.group(2)         
                        link_post = f"{self.FACEBOOK_BASE_URL}/{post_id}"

                slept_time = CommonUtils.sleep_random_in_range(3, 5)
                logger.debug(f"Slept {slept_time}")
                if link_post in self.link_posts:
                    # if iDem == 0:
                    #     iDem += 1
                    #     logger.info("Đã lấy hết các bài viết mới.")
                    #     CommonUtils.sleep_random_in_range(3,4)
                    #     continue
                    # elif iDem == 1:
                        # CommonUtils.sleep_random_in_range(3,4)
                        # check_out = False
                    CommonUtils.sleep_random_in_range(2,4)
                self.link_posts.append(link_post)
                
                ##push vào queue
                if self.q_posts_group.full():
                    logger.warning("Hàng đợi đã đầy")
                    slept_time = CommonUtils.sleep_random_in_range(300, 500)
                    logger.debug(f"Slept {slept_time}")
                else:
                    ##ghi vào file để back up
                    write_data_to_file(f"db/Search/{self.keyword.replace(' ', '_')}.txt", str(link_post))
                    self.queueLock.acquire()
                    self.q_posts_group.put(str(link_post))
                    self.queueLock.release()

                # self._scroll()
                if id_element >= (post_element_iterator._len() - 1):
                    slept_time = CommonUtils.sleep_random_in_range(5, 10)
                    logger.debug(f"Slept {slept_time}")
                    post_element_list = self._get_elements_by_xpath(self.POST_XPATH)
                    post_element_iterator.update(post_element_list=post_element_list)
                    logger.info(f"Số bài viết trên giao diện search là {post_element_iterator._len()}")

                if id_element % 20 == 0 and id_element !=0:
                    slept_time = CommonUtils.sleep_random_in_range(60, 120)
                    logger.debug(f"Slept {slept_time}")
            except StopIteration:
                logger.info(f"Đã hết post của trong phần search")
                break


class PostSearchExFromLink():
    driver: WebDriver

    POST_XPATH: str = './/div[@aria-posinset="1"]'
    POST_SHARE_XPATH: str = ".//div[@class='x1y332i5']"
    LINK_POST_SHARE_XPATH: str = ".//span[not(@class)]//a[contains(@class, 'xt0b8zv xo1l8bm') and @tabindex and @role='link']"
    posts: List[Post] = []
    callback: Optional[Callable[[Post], None]] = None
    post_crawl_done = []
    count_post_ex = 0
    MAX_SIZE_POST = 1000
    
    def __init__(self, driver: WebDriver, type: str, keyword: str, keyword_noparse: List ,share_queue: queue.Queue(), callback: Optional[Callable[[Post], None]] = None, ) -> None:
        self.callback = callback
        self.driver = driver
        self.type = type
        self.action = ActionChains(driver)
        self.q_posts_group = share_queue
        self.keyword = keyword
        self.keyword_noparse = keyword_noparse
        self.queueLock = threading.Lock()

    def _get_element_by_xpath(self, XPATH_, parent_element: Optional[WebElement] = None):
        try:
            self.driver.implicitly_wait(5)
            parent_element = parent_element if parent_element else self.driver
            return parent_element.find_element(by=By.XPATH, value=XPATH_)
        except NoSuchElementException as e:
            logger.error(f"Not found {XPATH_}")
            return None
        except Exception as e:
            logger.error(e, exc_info=True)
            return None


    def _enter_post_share(self, post_element: WebElement):
        logger.info("Start")
        try:
            a_post_content_element = post_element.find_element(By.XPATH, value=".//span[not(@class)]//a[contains(@class, 'xt0b8zv xo1l8bm') and @tabindex and @role='link']")
            # ActionChains(self.driver).move_to_element(a_post_content_element).click().perform()
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", a_post_content_element)
            self.action.click(a_post_content_element).perform()
            # a_post_content_element.click()
        except NoSuchElementException:
            logger.error(f"Not found xpath enter post share")
            return None
        except Exception as e:
            logger.error(e, exc_info=True)
            return None
        logger.info(f"End")
        return 1

    def unsigned_text(self, content : str):
        return unidecode(content).lower()
    
    def get_key_subkey(self, keyword_list_raw: str) -> List[str]:
        keyword_list_raw_dict = json.loads(keyword_list_raw)
        keyword_list = []
        subkey_list  = []
        # Lặp qua mỗi dict trong danh sách
        for item in keyword_list_raw_dict:
            item_key = {}
            # Lấy giá trị của key
            key = item['key']
            item_key['key'] = self.unsigned_text(key)
            # Lặp qua mỗi giá trị trong subKey
            for subkey in item['subKey']:
                subkey_list.append(self.unsigned_text(subkey))
                # Thêm từ khóa kết hợp vào danh sách keywords
            item_key['subkey'] = subkey_list
            keyword_list.append(item_key)

        return keyword_list
    

    def _get_link_post_share(self, element):
        link_post_share = ""
        element_link = self._get_element_by_xpath(self.LINK_POST_SHARE_XPATH, element)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element_link)
        #element_link.click()
        self.action.move_to_element(element_link).perform()
        CommonUtils.sleep_random_in_range(1,4)
        element_link = self._get_element_by_xpath(self.LINK_POST_SHARE_XPATH, element)
        link_post_share = element_link.get_attribute("href")
        # time_post = element_link.accessible_name

        return link_post_share
    
    def start(self):
        bCheck = True
        logger.info("--Start get post search---")
        key_unsigned = self.get_key_subkey(self.keyword_noparse)
        while bCheck:
            try:
                self.queueLock.acquire()
                logger.info(f"Size of queue {self.q_posts_group.qsize()}")
                if self.q_posts_group.empty():
                    self.queueLock.release()
                    slept_time = CommonUtils.sleep_random_in_range(60, 120)
                    logger.debug(f"Slept {slept_time}")
                    continue
                link_post = self.q_posts_group.get()
                self.queueLock.release()

                #ghi link post vào file _done.txt
                write_data_to_file(path_file=f"db/Search/{self.keyword.replace(' ', '_')}_done.txt", message=link_post)

                # link_post = link_post.replace("//www.", "//m.")
                self.driver.get(link_post)
                slept_time = CommonUtils.sleep_random_in_range(2, 5)
                logger.debug(f"Slept {slept_time}")
                post_element = self._get_element_by_xpath(XPATH_=self.POST_XPATH)

                if post_element:
                    post_share_element = self._get_element_by_xpath(XPATH_=self.POST_SHARE_XPATH)
                    # isPostShare = True if post_share_element else False
                    link_post_share = ""
                    if post_share_element:
                        link_post_share = self._get_link_post_share(element=post_share_element)
                    post_extractor: PostDesktopExtractor = PostDesktopExtractor(driver=self.driver, post_element=post_element, type=self.type)
                    post = post_extractor.extract()
                    retry_time = 0
                    def retry_extract(post, retry_time):
                        while not post.is_valid():
                            post = post_extractor.extract()
                            if retry_time > 0:
                                logger.debug(f"Try to extract post {retry_time} times {str(post)}")
                                slept_time = CommonUtils.sleep_random_in_range(1, 5)
                                logger.debug(f"Slept {slept_time}")
                            retry_time = retry_time + 1
                            if retry_time > 1:
                                logger.debug("Retried 20 times, skip post")
                                break
                        return
                    retry_extract(post, retry_time)
                        # lọc những bài viết không liên quan đến từ khóa
                    def filter_post(post):
                        logger.debug("-----______----------")
                        contents_unsigned = self.unsigned_text(post.content)
                        for item_key in key_unsigned:
                            if item_key['key'] in contents_unsigned:
                                for sub_k in item_key['subkey']:
                                    if sub_k in contents_unsigned:
                                        self.posts.append(post)
                                        break
                    filter_post(post)

                    self.posts.append(post)
                    self.count_post_ex += 1

                    if link_post_share:
                        # enter_post = self._enter_post_share(post_share_element)
                        self.driver.get(link_post_share) 
                        slept_time = CommonUtils.sleep_random_in_range(1, 3)
                        logger.debug(f"Slept {slept_time}")
                        post_share_element = self._get_element_by_xpath(XPATH_=self.POST_XPATH)
                        slept_time = CommonUtils.sleep_random_in_range(1, 5)
                        logger.debug(f"Slept {slept_time}")
                        if post_share_element:
                            post_share_extractor: PostDesktopExtractor = PostDesktopExtractor(driver=self.driver, post_element=post_share_element, source_id=post.id, type="facebook share")
                            post_share = post_share_extractor.extract()
                            retry_time = 0
                            retry_extract(post_share, retry_time)
                            filter_post(post_share)

                            self.posts.append(post_share)
                            self.count_post_ex += 1

                            slept_time = CommonUtils.sleep_random_in_range(2, 10)
                            logger.debug(f"Slept {slept_time}")

                    logger.info(f"Số bài viết đã extractor {self.count_post_ex}")

                    if self.callback:
                        self.callback(post)
                    #Check xem số bài viết đã đủ 20 chưa, nếu đủ trả về để đẩy qua kafka
                    if len(self.posts) %20 == 0 and len(self.posts) != 0:
                        yield self.posts
                        self.posts = []
                        slept_time = CommonUtils.sleep_random_in_range(200, 300)
                        logger.debug(f"Slept {slept_time}")
                    #Check xem số bài viết đã vượt giới hạn chưa
                    if self.count_post_ex > self.MAX_SIZE_POST:
                        logger.warning("Đã lấy đủ số lượng bài ưu cầu")
                        break
                
            except Exception as ex:
                logger.error(ex)
                bCheck = False


