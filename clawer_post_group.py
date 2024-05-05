"""
Author: QuanDV
Description: Get posts group
"""


from typing import Callable, List, Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from post_extractor import PostExtractor
from post_desktop_extractor import PostDesktopExtractor
from selenium_utils import SeleniumUtils
from utils.log_utils import logger
from utils.common_utils import CommonUtils
from post_model import Post
import json
from unidecode import unidecode
from post_search_extractor import PostElementIterator
from selenium.webdriver import ActionChains
from bs4 import BeautifulSoup
from utils.utils import write_data_to_file, read_data_from_file
import queue
import threading

from queue import Empty

#todo lấy path post trong nhóm, trang
class PostsDesktopGroupExtractor:
    driver: WebDriver
    # todo xử lý lại đường dẫn tại đây, chỉnh từ page sang group phù hợp là có thể cào được
    GROUP_FACEBOOK_DESKTOP: str = "https://www.facebook.com/"
    POST_XPATH: str = "//div[@aria-posinset and @aria-describedby]"
    LINK_POST_XPATH: str = './/a[contains(@class, "xt0b8zv xo1l8bm") and @tabindex and @role="link"]'

    #Danh sách post
    link_posts: List[Post] = []
    #hàm không trả về giá trị
    callback: Optional[Callable[[Post], None]] = None
    def __init__(self, driver: WebDriver, group_id : str, share_queue: queue.Queue(), callback: Optional[Callable[[Post], None]] = None) -> None:
        self.group_id = group_id
        self.group_link = self.GROUP_FACEBOOK_DESKTOP + group_id + "?sorting_setting=CHRONOLOGICAL"
        self.callback = callback
        self.driver = driver
        self.actions = ActionChains(driver)
        self.q_posts_group = share_queue
        self.queueLock = threading.Lock()

        print("groupID", group_id)
        print("group_link", self.group_link)
        try:
            #todo đọc dữ liệu tại 2 file
            self.link_posts_all = read_data_from_file(path_file=f"db/Groups/{group_id}.txt")
            self.link_crawl_done = read_data_from_file(f"db/Groups/{group_id}_done.txt")

            #todo lấy từng link đã lưu trong file
            for link_ in self.link_posts_all:
                #todo xử lý cho các bài chưa xử lý
                if link_ not in self.link_crawl_done:
                    if self.q_posts_group.full():
                        logger.warning("Hàng đợi đã đầy")
                        
                        slept_time = CommonUtils.sleep_random_in_range(1000, 2000)
                        logger.debug(f"Slept {slept_time}")

                    #todo xử lý khi hàng đợi vẫn còn
                    else:
                        print(link_)
                        self.queueLock.acquire()
                        self.q_posts_group.put(link_)
                        self.queueLock.release()
                        self.link_posts.append(link_)
        except Exception as e:
            print('err', e)
#             logger.warning(f"File not found {group_id}.txt")
            self.link_posts = []

        self.driver.get(self.group_link)
        self.driver.implicitly_wait(1000)
        self._scroll()
        slept_time = CommonUtils.sleep_random_in_range(1, 5)
        logger.debug(f"Slept {slept_time}")

    #todo action scroll trong page
    def _scroll(self):
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.driver.implicitly_wait(3)
        except Exception as e:
            logger.error(e)

    #todo lấy đối tượng theo xPath
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
        logger.warning("get link posts")
        post_element_list = self._get_elements_by_xpath(self.POST_XPATH)
        post_element_iterator = PostElementIterator(post_element_list=post_element_list)
        iDem = 0
        #hàm lấy link bài viết từ các post element
        def _get_link_from_post_element(element):
            #self.driver.execute_script("arguments[0].scrollIntoView(true);", element)

            #############
            element_link = self._get_element_by_xpath(self.LINK_POST_XPATH, element)
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element_link)
            #element_link.click()
            self.actions.move_to_element(element_link).perform()
            CommonUtils.sleep_random_in_range(1,4)
            element_link = self._get_element_by_xpath(self.LINK_POST_XPATH, element)
            link_post = element_link.get_attribute("href")
            time_post = element_link.accessible_name
            ## check xem bài viết quá time hay chưa

            #vượt quá thời gian (config cứng) sẽ không trả về bài
           
            return link_post
        
        id_element = 0
        
        check_out = True
        while check_out:
            try:
                element = next(post_element_iterator)
                id_element = post_element_iterator.index
                link_post = _get_link_from_post_element(element=element)
                slept_time = CommonUtils.sleep_random_in_range(3, 7)
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
                    write_data_to_file(f"db/Groups/{self.group_id}.txt", str(link_post))
                    self.queueLock.acquire()
                    self.q_posts_group.put(str(link_post))
                    self.queueLock.release()

                #self._scroll()
                if id_element >= (post_element_iterator._len() - 1):
                    slept_time = CommonUtils.sleep_random_in_range(5, 10)
                    logger.debug(f"Slept {slept_time}")
                    post_element_list = self._get_elements_by_xpath(self.POST_XPATH)
                    post_element_iterator.update(post_element_list=post_element_list)
                    logger.info(f"Số bài viết trên giao diện group là {post_element_iterator._len()}")


                if id_element % 20 == 0 and id_element !=0:
                    slept_time = CommonUtils.sleep_random_in_range(60, 120)
                    logger.debug(f"Slept {slept_time}")
            except StopIteration as e:
                logger.info(f"Đã hết post của trong group")
                break


class PostGroupDeskopExFromLink():
    driver: WebDriver

    POST_XPATH: str = './/div[@aria-posinset="1"]'
    POST_SHARE_XPATH: str = ".//div[@class='x1y332i5']"
    LINK_POST_SHARE_XPATH: str = ".//span[not(@class)]//a[contains(@class, 'xt0b8zv xo1l8bm') and @tabindex and @role='link']"
    posts: List[Post] = []
    callback: Optional[Callable[[Post], None]] = None
    post_crawl_done = []
    count_post_ex = 0
    MAX_SIZE_POST = 1000
    
    def __init__(self, driver: WebDriver, type:str, group_id : str, share_queue: queue.Queue(), callback: Optional[Callable[[Post], None]] = None, ) -> None:
        self.callback = callback
        self.driver = driver
        self.type = type
        self.group_id = group_id
        self.action = ActionChains(driver)
        self.q_posts_group = share_queue
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
        logger.info("--Start get post group---")
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
                write_data_to_file(path_file=f"db/Groups/{self.group_id}_done.txt", message=link_post)

                # link_post = link_post.replace("//www.", "//m.")
                self.driver.get(link_post)
                slept_time = CommonUtils.sleep_random_in_range(2, 5)
                logger.debug(f"Slept {slept_time}")
                post_element = self._get_element_by_xpath(XPATH_=self.POST_XPATH)

                #todo Xử lý khi có bài post
                if post_element:
                    post_share_element = self._get_element_by_xpath(XPATH_=self.POST_SHARE_XPATH)
                    # isPostShare = True if post_share_element else False
                    link_post_share = ""
                    if post_share_element:
                        link_post_share = self._get_link_post_share(element=post_share_element)

                    #todo lấy thông tin từ bài post

                    #kiểm tra xem bài viết có chứa keyword hay không  -> có thì xử lý, không thì bỏ qua
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
                            post_share_extractor: PostDesktopExtractor = PostDesktopExtractor(driver=self.driver, post_element=post_share_element, source_id=post.id, type="facebook share ")
                            post_share = post_share_extractor.extract()
                            retry_time = 0
                            retry_extract(post_share, retry_time)

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