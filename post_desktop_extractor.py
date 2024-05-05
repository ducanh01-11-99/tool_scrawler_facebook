import datetime
from typing import List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from post_extractor import PostExtractor
from utils.log_utils import logger
import json
import re
import time
import calendar
import traceback
from post_model import Post
from selenium_utils import SeleniumUtils
from utils.common_utils import CommonUtils
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from datetime import datetime, timedelta, date
from jsonpath_ng import jsonpath, parse
from utils.common_utils import ElementIterator
from confluent_kafka import Consumer
from confluent_kafka import Producer
consumer = Consumer({
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'my-group',
    'auto.offset.reset': 'earliest'  # Bắt đầu tiêu thụ từ đầu
})

consumer.subscribe(['test'])

class PostDesktopExtractor(PostExtractor):
    POST_INFOR_XPATH: str = '//script[contains(text(), "UFI2Config")]'
    POST_PHOTO_XPATH: str = ".//div[@class='x1n2onr6' and @id]//div[@class='x1n2onr6']//a"
    POST_COMMENT_CONTENT_XPATH: str = ".//div[@role='article' and @aria-label]"
    POST_COMMENT_AREA_XPATH: str = ".//div[@data-visualcompletion='ignore-dynamic' and @class]"
    COMMENT_ID_REGEX_PATTERN = r"(?:reply_)?comment_id=(\d+)"


    def __init__(self, post_element: WebElement, driver: WebDriver, source_id="", type=""):
        super().__init__(post_element=post_element, driver=driver)
        self.post_data = self.extract_post_infor()
        self.actions = ActionChains(driver)
        self.source_id = source_id
        self.type = type

    def _get_elements_by_xpath(self, XPATH_, parent_element: Optional[WebElement] = None):
        try:
            self.driver.implicitly_wait(5)
            parent_element = parent_element if parent_element else self.post_element
            return parent_element.find_elements(by=By.XPATH, value=XPATH_)
        except NoSuchElementException as e:
            logger.error(f"Not found {XPATH_}")
            return None
        except Exception as e:
            logger.error(e, exc_info=True)
            return None

    def _get_element_by_xpath(self, XPATH_, parent_element: Optional[WebElement] = None):
        try:
            self.driver.implicitly_wait(1)
            parent_element = parent_element if parent_element else self.post_element
            return parent_element.find_element(by=By.XPATH, value=XPATH_)
        except NoSuchElementException as e:
            logger.warning(f"Not found {XPATH_}")
            return None
        except Exception as e:
            logger.error(e, exc_info=True)
            return None

    def extract_post_infor(self):
        logger.info("Start")
        json_data = {}
        post_infor_element = self._get_element_by_xpath(XPATH_=self.POST_INFOR_XPATH)
        if post_infor_element:
            infor_json = post_infor_element.get_attribute('innerHTML')
            try:
                json_data = json.loads(infor_json)
                jsonpath_expr = parse("$..result.data.node")
                match = jsonpath_expr.find(json_data)
                if match:
                    json_data = match[0].value
            except Exception as e:
                logger.error(e)
            logger.info("End")
        else:
            logger.error(f"Not found {self.POST_INFOR_XPATH}")
        return json_data


    def extract_post_id(self)-> Optional[str]:
        logger.info("Start")
        self.post_id = self.post_data["post_id"]
        logger.info("End")
        return self.post_id

    def extract_post_author(self):
        logger.info("Start")
        post_author: str = ''
        post_author_link: str = ''
        post_author_avatar_link: str = ''
        json_path = parse("$..content..actor_photo.story.actors")
        matches = json_path.find(self.post_data)
        if matches:
            author_data = matches[0].value
            post_author_link = author_data[0]["url"]
            post_author = author_data[0]["name"]
            post_author_avatar_link = author_data[0]["profile_picture"]["uri"]
            logger.info("End")
        else:
            logger.error("cannot extract post author info")
        return post_author, post_author_link, post_author_avatar_link

    def extract_post_content(self) -> str:
        logger.info("Start")
        post_content_str: str = ''
        hashtag: List[str] = []
        json_path = parse("$..content..rich_message")
        matches = json_path.find(self.post_data)
        if matches:
            content_data = matches[0].value
            for content in content_data:
                text = content["text"]
                post_content_str += text + " "
                for entity_range in content["entity_ranges"]:
                    if "entity" in entity_range:
                        url_hashtag = entity_range["entity"]["url"]
                        pattern = r'https://www.facebook.com/hashtag/([^/?]+)\?'
                        match = re.search(pattern, url_hashtag)
                        if match:
                            hashtag_text = match.group(1)
                            hashtag.append(hashtag_text)
            # post_content_str = content_data["text"]
            logger.info("End")
        else:
            json_path = parse("$..content.story.comet_sections.message.story.message")
            matches = json_path.find(self.post_data)
            if matches:
                content_data = matches[0].value
                post_content_str = content_data["text"]
                logger.info("End")
            else:
                logger.error("cannot extract post content")
        return post_content_str, hashtag

    def extract_post_time(self) -> str:
        logger.info("Start")
        post_time: str = ''
        json_path = parse("$..content..creation_time")
        matches = json_path.find(self.post_data)
        if matches:
            post_time = matches[0].value
            logger.info("End")
        else:
            logger.error("cannot extract post tỉme")
        return post_time

    def extract_post_link(self) -> str:
        logger.info("start")
        post_link: str = ""
        json_path = parse("$..metadata")
        matches = json_path.find(self.post_data)
        if matches:
            metadata = matches[0].value
            for item in metadata:
                if "story" in item and "url" in item["story"]:
                    post_link = item["story"]["url"]
                    break
            logger.info("End")
        else:
            logger.error("cannot extract post link")
        return post_link

    def extract_post_reactions(self):
        logger.info("Start")
        reactions = {
            "like" : 0,
            "share" : 0,
            "haha" : 0,
            "wow" : 0,
            "sad" : 0,
            "love" : 0,
            "angry" : 0,
            "care" : 0
        }
        # require[0][3][0].__bbox.require[99][3][1].__bbox.result.data.node.comet_sections.feedback.story.comet_feed_ufi_container.story.story_ufi_container.story.feedback_context.feedback_target_with_context.comet_ufi_summary_and_actions_renderer.feedback.top_reactions
        json_path = parse("$..comet_ufi_summary_and_actions_renderer.feedback.top_reactions")
        matches = json_path.find(self.post_data)
        if matches:
            reactions_data = matches[0].value
            for item in reactions_data["edges"]:
                reaction_name = item["node"]["localized_name"]
                reaction_count = item["reaction_count"]
                reaction_name = reaction_name.lower()
                reactions[reaction_name] = reaction_count
            logger.info("End")
        else:
            logger.error("cannot extract post reactions")
        return reactions


    def extract_post_comment(self):
        logger.info("Start")
        comment = 0
        json_path = parse("$..comment_list_renderer.feedback.total_comment_count")
        matches = json_path.find(self.post_data)
        if matches:
            comment = matches[0].value
            # comment = comment_data["total_count"]
            logger.info("End")
        else:
            logger.error("cannot extract post comment_count")
        return comment

    def extract_post_share(self):
        logger.info("Start")
        share = 0
        json_path = parse("$..share_count")
        matches = json_path.find(self.post_data)
        if matches:
            share_data = matches[0].value
            share = share_data["count"]
            logger.info("End")
        else:
            logger.error("cannot extract post share_count")
        return share

    def extract_post_photos(self):
        logger.info("Start")
        post_photos = []
        video_links = []

        imgs = self._get_elements_by_xpath(XPATH_=self.POST_PHOTO_XPATH)
        if imgs:
            for img in imgs:
                image_element = self._get_element_by_xpath(XPATH_=".//img", parent_element=img)
                if image_element:
                    image_url = image_element.get_attribute('src')
                    post_photos.append(image_url)
                else:
                    try:
                        video_element = img.find_element(By.TAG_NAME, value="video")
                        video_link = video_element.get_attribute("src")
                        video_links.append(video_link)
                    except NoSuchElementException:
                        logger.warning("not found tag_name video")
                    except Exception as e:
                        logger.error(e, exc_info=True)

            photo_plus = imgs[-1].text
            if "+" in photo_plus and len(imgs) > 4:
                try:
                    photo_plus = int(photo_plus.split("+")[-1])
                    SeleniumUtils.click_element(driver=self.driver, element=imgs[-1])
                    slept_time = CommonUtils.sleep_random_in_range(1, 5)
                    logger.debug(f"Slept {slept_time}")

                    self.actions.send_keys(Keys.ARROW_RIGHT).perform()
                    for i in range(photo_plus-1):
                        slept_time = CommonUtils.sleep_random_in_range(1, 5)
                        logger.debug(f"Slept {slept_time}")
                        image_element = self._get_element_by_xpath(XPATH_="//img[@data-visualcompletion]", parent_element=self.driver)
                        if image_element:
                            image_url = image_element.get_attribute('src')
                            post_photos.append(image_url)
                        else:
                            video_element = self._get_element_by_xpath(XPATH_="//a//video", parent_element=self.driver)
                            if video_element:
                                video_link = video_element.get_attribute("src")
                                video_links.append(video_link)
                            else:
                                logger.error("not found image or video")
                        self.actions.send_keys(Keys.ARROW_RIGHT).perform()

                    self.actions.send_keys(Keys.ESCAPE).perform()
                except Exception as e:
                    logger.error(e)
        logger.info("End")
        return post_photos, video_links

    def _parse_comment(self, comment_element: WebElement) -> dict:
        comment_post = Post()
        commenter_name: str = ""
        commenter_url: str = ""
        commenter_avata: str = ""

        # commenter_element = comment_element.find_element(By.XPATH, value=".//a[@aria-hidden='false']")
        commenter_name_element = self._get_element_by_xpath(XPATH_=".//a[@aria-hidden='false']", parent_element=comment_element)
        if commenter_name_element:
            commenter_name = commenter_name_element.text
            commenter_url = commenter_name_element.get_attribute("href")
        else:
            logger.error("not found commenter_name_element")

        commenter_avatar_element = self._get_element_by_xpath(XPATH_="./div[1]", parent_element=comment_element)
        if commenter_avatar_element:
            try:
                commenter_image_element = commenter_avatar_element.find_element(By.TAG_NAME, value="image")
                commenter_avata = commenter_image_element.get_attribute("xlink:href")
            except NoSuchElementException:
                logger.error("not found commenter_image_element")
            except Exception as e:
                logger(e)
        else:
            logger.error("not found commenter_avatar_element")

        comment_id, reply_comment_id, comment_time = self.extract_comment_time(comment_element)
        comment_content = self.extract_comment_content(comment_element)
        comment_image = self.extract_comment_image(comment_element)
        comment_video = self.extract_comment_video(comment_element)
        reactions_comment = self.extract_comment_reactions(comment_element)

        if reply_comment_id != "":
            comment_post.id = reply_comment_id
            comment_post.source_id = comment_id
        else:
            comment_post.id = comment_id
            comment_post.source_id = self.post_id
        comment_post.type = "facebook comment"
        comment_post.author = commenter_name
        comment_post.author_link = commenter_url
        comment_post.avatar = commenter_avata
        comment_post.content = comment_content
        comment_post.link = f"https://www.facebook.com/{comment_post.id}"
        comment_post.created_time = self.convert_text_to_datetime(comment_time)
        comment_post.image_url = comment_image
        comment_post.video = comment_video
        comment_post.like, comment_post.comment, comment_post.haha, comment_post.wow, comment_post.sad, comment_post.love, comment_post.angry, comment_post.share = reactions_comment['like'], reactions_comment['comment'], reactions_comment['haha'] ,reactions_comment['wow'] , reactions_comment['sad'], reactions_comment['love'] ,reactions_comment['angry'] ,reactions_comment['share']
        comment_post.time_crawl = datetime.now()
# ===================_______________=======================#
        self.on_post_available_callback(comment_post)
        return comment_post


    def extract_comment_time(self, comment_element: WebElement):
        logger.info("Start")
        comment_id: str = ""
        reply_comment_id: str = ""
        comment_time_create: str = ""

        comment_time_element = self._get_element_by_xpath(XPATH_=".//ul//a", parent_element=comment_element)
        if comment_time_element:
            comment_time_create = comment_time_element.text.lower()
            comment_id_url = comment_time_element.get_attribute("href")
            match = re.findall(pattern=self.COMMENT_ID_REGEX_PATTERN, string=comment_id_url)
            if match:
                if (len(match)) == 1:
                    comment_id = match[0]
                else:
                    comment_id, reply_comment_id = match
            else:
                logger.error(f"Not found regex {self.COMMENT_ID_REGEX_PATTERN} in link {comment_id_url}")
        else:
            logger.error("not found comment_time_element")
        return comment_id, reply_comment_id, comment_time_create


    def extract_comment_content(self, comment_element: WebElement) -> str:
        logger.info("Start")
        comment_content: str = ""
        comment_content_element = self._get_element_by_xpath(XPATH_=".//div/span[@dir='auto' and @class and ./div]", parent_element=comment_element)
        if comment_content_element:
            see_more_element = self._get_element_by_xpath(XPATH_=".//div[@role='button']", parent_element=comment_content_element)
            if see_more_element:
                see_more_element.click()
                self.driver.implicitly_wait(1)
                comment_content = comment_content_element.text
                logger.info("End")
            else:
                comment_content = comment_content_element.text
                logger.info("End")
        else:
            logger.error("not found comment_content_element")
        return comment_content

    def extract_comment_image(self, comment_element: WebElement):
        logger.info("Start")
        image_links = []
        comment_img_element = self._get_element_by_xpath(XPATH_=".//a//img[@alt and @referrerpolicy]", parent_element=comment_element)
        if comment_img_element:
            image_url = comment_img_element.get_attribute('src')
            image_links.append(image_url)
            logger.info("End")
        return image_links


    def extract_comment_video(self, comment_element: WebElement):
        logger.info("Start")
        video_links = []
        comment_video_element = self._get_element_by_xpath(XPATH_=".//video[@class and @src]", parent_element=comment_element)
        if comment_video_element:
            image_url = comment_video_element.get_attribute('src')
            video_links.append(image_url)
            logger.info("End")
        return video_links

    def extract_comment_reactions(self, comment_element: WebElement):
        logger.info("Start")
        reactions = {
            "like" : 0,
            "share" : 0,
            "haha" : 0,
            "wow" : 0,
            "sad" : 0,
            "love" : 0,
            "angry" : 0,
            "care" : 0,
            "comment" : 0
        }
        reaction_list = ["like", "haha", "wow", "sad", "love", "angry", "care"]
        comment_icon_element = self._get_element_by_xpath(XPATH_=".//div[@aria-label[contains(., 'reacted')] and @role='button']", parent_element=comment_element)
        if comment_icon_element:
            SeleniumUtils.click_element(driver=self.driver, element=comment_icon_element)
            # self.driver.implicitly_wait(5)
            slept_time = CommonUtils.sleep_random_in_range(1, 3)
            logger.debug(f"Slept {slept_time}")
            reactions_tab_list_element = self._get_element_by_xpath(XPATH_=".//div[@aria-labelledby and @role='dialog']//div[@role='tablist']", parent_element=self.driver)
            if reactions_tab_list_element:
                # print(reactions_tab_list_element.get_attribute("innerHTML"))
                reactions_tab_elements = self._get_elements_by_xpath(XPATH_=".//div[@role='tab']", parent_element=reactions_tab_list_element)
                for tab in reactions_tab_elements[1:]:
                    reaction = tab.get_attribute("aria-label").lower()
                    reaction_type = reaction.split(",")[0].strip()
                    value = reaction.split(",")[1].strip()
                    if reaction_type in reaction_list:
                        reactions[reaction_type] = self.convert_to_number(value)
                self.actions.send_keys(Keys.ESCAPE).perform()
                self.driver.implicitly_wait(3)
                logger.info("End")
            else:
                logger.error("not found reactions_tab_list_element")
        return reactions

    def extract_post_comments(self):
        logger.info("start")
        post_comments = []
        # comment_area_element = self._get_comment_area_element()
        comment_area_element = self._get_element_by_xpath(XPATH_=self.POST_COMMENT_AREA_XPATH)
        if comment_area_element:
            self.driver.implicitly_wait(3)
            comment_area_element_list = self._get_elements_by_xpath(XPATH_=".//div[@class='x169t7cy x19f6ikt']", parent_element=comment_area_element)
            comment_element_iterator = ElementIterator(element_list=comment_area_element_list)
            while True:
                try:
                    comment = next(comment_element_iterator)
                    # action.move_to_element(comment).perform()
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", comment)
                    while True:
                        self.driver.implicitly_wait(5)
                        repCmt = self._get_element_by_xpath(XPATH_=".//div[@class='x78zum5 x1iyjqo2 x21xpn4 x1n2onr6']//div[@role='button' and not(contains(., 'Hide'))]", parent_element=comment)
                        if repCmt:
                            try:
                                self.actions.move_to_element(repCmt).click().perform()
                                self.driver.implicitly_wait(5)
                            except Exception as e:
                                logger.error(e)
                        else:
                            break

                    comment_content_list = self._get_elements_by_xpath(XPATH_=self.POST_COMMENT_CONTENT_XPATH, parent_element=comment)
                    for comment in comment_content_list:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", comment)
                        comment_post = self._parse_comment(comment_element=comment)
                        post_comments.append(comment_post)

                    if comment_element_iterator.index == (comment_element_iterator._len() - 1):
                        viewMoreCmt = self._get_element_by_xpath(XPATH_=".//div[@role='button' and contains(.,'View')]", parent_element=comment_area_element)
                        if viewMoreCmt:
                            self.actions.move_to_element(viewMoreCmt).click().perform()
                            slept_time = CommonUtils.sleep_random_in_range(5, 10)
                            logger.debug(f"Slept {slept_time}")
                            comment_area_element_list = self._get_elements_by_xpath(XPATH_=".//ul//li[not(@class) and not(ancestor::li)]", parent_element=comment_area_element)
                            comment_element_iterator.update(element_list=comment_area_element_list)
                except StopIteration as e:
                    logger.debug(f"Đã hết comment của bài post")
                    break
                except Exception as e:
                    logger.error(e)
                    break
        else:
            logger.error("Not found comment_area_element")
        return post_comments

    def convert_to_number(self,value):
        number = 0
        try:
            value = value.strip().lower()
            multipliers = {'k': 1000, 'm': 1000000}
            suffix = value[-1]
            if suffix in multipliers:
                number = float(value[:-1]) * multipliers[suffix]
            else:
                number = float(value)
        except Exception as ex:
            logger.error(ex)
        finally:
            return int(number)


    def on_post_available_callback(self, post: Post):
        data = {
            "content": post.content,
            "post_link": post.link,
            "author": post.author,
            "type": post.type,
            "author_link": post.author_link,
            "created_time": post.created_time,
            "share_number": post.share,
            "react_number": post.like,
            "comment_number": post.comment,
            "image_related_url": post.image_url,
            "evaluate": "positive",
            "avatar": post.avatar,
            "source_id": post.source_id,
            "id": post.id,
            "evaluate": "positive",
        }
        check = true
        print("postData", data)
        if check:
                    json_data = json.dumps(data).encode('utf-8')
                    producer = Producer({'bootstrap.servers': 'localhost:9092',  }) # Replace with your Kafka broker address
                    #check content có phù hợp không? có thì mới đẩy vào kafka
                    producer.produce('test', json_data)
                    # Flush the producer to send the message immediately
                    producer.flush()

                    print("Day post vào kafka")
                    with open("result.txt", "a", encoding="utf-8") as file:
                        file.write(f"{str(post)}\n")
                        # NguyenNH: in màu cho dễ debug
                        if post.is_valid:
                            file.write(f"🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷\n")
                        else:
                            file.write(f"🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈\n")

    def convert_text_to_datetime(self, text):
    # 1m, 1h, 1d, 1w, 1y
        current_time = datetime.now()
        if "m" in text:
            minutes = int(text.strip('m'))
            new_time = current_time - timedelta(minutes=minutes)
            new_time = new_time.replace(microsecond=0, second=0)
        elif "h" in text:
            hours = int(text.strip('h'))
            new_time = current_time - timedelta(hours=hours)
            new_time = new_time.replace(microsecond=0, second=0, minute=0)
        elif "d" in text:
            days = int(text.strip('d'))
            new_time = current_time - timedelta(days=days)
            new_time = new_time.replace(microsecond=0, second=0, minute=0, hour=0)
        elif "w" in text:
            weeks = int(text.strip('w'))
            new_time = current_time - timedelta(weeks=weeks)
            new_time = new_time.replace(microsecond=0, second=0, minute=0, hour=0)
        elif "y" in text:
            years = int(text.strip('y'))
            new_time = current_time - timedelta(years=years)
            new_time = new_time.replace(microsecond=0, second=0, minute=0, hour=0)

        timestamp = int(new_time.timestamp())
        return timestamp

