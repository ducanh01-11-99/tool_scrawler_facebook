import time
import config
import random
import sys
sys.path.append('/home/ducanh/.local/lib/python3.10/site-packages')
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

chrome_options = Options()
# chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("start-maximized")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--incognito')
#chrome_options.add_argument('--headless')
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument('--disable-infobars')
chrome_options.add_argument("--disable-dev-shm-usage")
# chrome_options.add_experimental_option("detach", True)
chrome_options.add_experimental_option(
    "prefs", {"profile.default_content_setting_values.notifications": 2})

#mobile_emulation = {
#    "deviceMetrics": { "width": 360, "height": 640, "pixelRatio": 3.0 },
#    "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile Safari/535.19" }

#chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)


class WebBrowser:
    def __init__(self, proxy=None, path_dir_chrome_driver=config.CHROMEDRIVER_PATH):
        self.driver = None
        self.path_dir_chrome_driver = path_dir_chrome_driver
        self.proxy = proxy
        self.init_browser_chrome()

    def init_browser_chrome(self):
        if self.proxy is not None:
            chrome_options.add_argument('--proxy-server=%s' % self.proxy)
            # self.driver = webdriver.Chrome(options=chrome_options, executable_path=self.path_dir_chrome_driver)
            self.driver = webdriver.Chrome('/home/ducanh/Downloads/chromedriver-linux64/chromedriver')
        

    def get_url(self, url):
        try:
            url = "https://facebook.com"
            self.driver.get(url)
            self.driver.implicitly_wait(1000)
            time.sleep(2)
            if str(self.driver.title).find("Facebook") == -1:
                print("Facebook not in title")
                self.get_url(url=config.url_facebook)
        except Exception as e:
            print("Exception: get url: " + str(e))
            self.get_url(url=config.url_facebook)

    def go_url_with_keyword(self, url):
        self.driver.get(url)
        self.driver.implicitly_wait(1000)

    def login_fb_with_cookie(self, cookie):
        script = 'javascript:void(function(){ function setCookie(t) { var list = t.split("; "); console.log(list); ' \
                 'for (var i = list.length - 1; i >= 0; i--) { var cname = list[i].split("=")[0]; var cvalue = list[' \
                 'i].split("=")[1]; var d = new Date(); d.setTime(d.getTime() + (7*24*60*60*1000)); var expires = ' \
                 '";domain=.facebook.com;expires="+ d.toUTCString(); document.cookie = cname + "=" + cvalue + "; " + ' \
                 'expires; } } function hex2a(hex) { var str = ""; for (var i = 0; i < hex.length; i += 2) { var v = ' \
                 'parseInt(hex.substr(i, 2), 16); if (v) str += String.fromCharCode(v); } return str; } setCookie("' \
                 + cookie + '"); location.href = "https://facebook.com"; })(); '
        self.driver.execute_script(script)
        # time.sleep(2)
        # print(self.check_fb_2fa())
        return 1

    def check_fb_2fa(self):
        try:
            if self.driver.execute_script(
                    "return document.body.querySelector('form').textContent.includes(\"Two-factor authentication "
                    "required\")"):
                return True
            return False
        except Exception as e:
            print("Exception: check_fb_2fa: " + str(e))
            return False

    def login_fb_with_username(self, username, password):
        self.driver.execute_script(
            "document.body.querySelector('div#content.fb_content.clearfix').querySelector('form').querySelector("
            "'input#email').value =\"" + username + "\";")
        time.sleep(random.uniform(0.1, 0.5))
        self.driver.execute_script(
            "document.body.querySelector('div#content.fb_content.clearfix').querySelector('form').querySelector("
            "'input#pass').value=\"" + password + "\";")
        time.sleep(random.uniform(0.5, 0.75))
        self.driver.execute_script(
            "document.body.querySelector('div#content.fb_content.clearfix').querySelector('form').querySelector("
            "'button').click()")
        time.sleep(1)
        return 1

    def login(self, email, pswrd):
        elem = self.driver.find_element(By.ID, "email")
        elem.send_keys(email)
        elem = self.driver.find_element(By.ID, "pass")
        elem.send_keys(pswrd)
        elem.send_keys(Keys.RETURN)

    def ok(self):
        self.driver.implicitly_wait(20)
        elem = self.driver.find_element_by_xpath("//input[@value='OK']")
        elem.send_keys(Keys.RETURN)
        print("[Browser] ok successful.")

    def search_by(self, search_keyword):
        try:
            elem = self.driver.find_element_by_name("T&#xec;m ki&#x1ebf;m")
            elem.send_keys(search_keyword)
            # self.driver.implicitly_wait(20)
            elem.send_keys(Keys.RETURN)
            print(f"[Browser] Searching by keyword {search_keyword}")
        except:
            print("[Error] Error searching by keyword")

    def filter_by(self, filter_name):
        self.driver.implicitly_wait(10)
        try:
            filter_groups = self.driver.find_element_by_partial_link_text(
                filter_name)
            filter_groups.click()
            print("[Browser] Filter applied")
        except NoSuchElementException as e:
            print(f"[Error] Couldn't find the selector {filter_name}. - {e}")

    def sort_by(self, sort_param):
        try:
            sort_by_recent = self.driver.find_element_by_partial_link_text(
                sort_param)
            sort_by_recent.click()
            print("[Browser] Sorted.")
        except NoSuchElementException as e:
            print(
                f"[Error] Couldn't find the sorting parameter {sort_param}. - {e}"
            )

    def get_source(self):
        return self.driver.page_source.encode('utf-8')

    def scroll_page(self, iCount):
        for id in range(int(iCount)):
            ids = id + 1
            iX = ids * 2000
            iY = (ids + 1) * 2000
            self.driver.execute_script("window.scrollTo(" + str(iX) + ", " + "window.scrollY + " + str(iY) + ")")
            time.sleep(3)

    def click_continue(self):
        WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[@id='checkpointSubmitButton']"))).click()

    def submit_2fakey_to_fb(self, key2fa):
        try:
            self.driver.find_element_by_id('approvals_code').send_keys(key2fa)
            # click submit code
            # checkpointSubmitButton-actual-button for mbasic
            # checkpointSubmitButton for facebook
            self.click_continue()
            time.sleep(2)
            # click continue
            self.click_continue()
            time.sleep(2)
            if str(self.driver.page_source.encode('utf-8')).find(
                    "Someone recently") != -1:
                self.click_continue()
                time.sleep(2)
                self.click_continue()
                time.sleep(2)
                self.click_continue()
                time.sleep(2)
        except:
            print("error submit key2fa")
            self.submit_2fakey_to_fb(key2fa)

    def submitKeyIn2FA(self, string_2fa):
        try:
            self.driver.find_element_by_id("listToken").clear()
            self.driver.find_element_by_id('listToken').send_keys(string_2fa)

            # click submit get key2fa
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//*[@id='submit']"))).click()

            time.sleep(2)

            contents = self.driver.find_element_by_id('output').get_attribute(
                'value')

            key2fa = contents.split("|")[1]

        except:
            print("Error submit 2fa key")
            return self.submitKeyIn2FA(string_2fa)

        return key2fa

    def swicthTabsubmitKey(self, fa_key):
        url = "http://2fa.live/"

        self.driver.execute_script("window.open('');")

        # Switch to the new window
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.get(url)

        # get key2fa from 2fa
        key2fa = self.submitKeyIn2FA(fa_key)

        self.driver.close()
        self.driver.switch_to_window(self.driver.window_handles[0])

        # submit key2fa in fb
        self.submit_2fakey_to_fb(key2fa)

    # HoangLM: get k2fa
    def get_k2FA(self, fa_key):
        url = "http://2fa.live/"

        self.driver.execute_script("window.open('');")

        # Switch to the new window
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.get(url)

        # get key2fa from 2fa
        key2fa = self.submitKeyIn2FA(fa_key)
        return key2fa

    def is_2fa_require(self):
        try:
            if self.driver.execute_script(
                    "return document.body.querySelector('form').textContent.includes(\"Two-factor authentication required\")"):
                return True
            return False
        except:
            return False

    def check2StepValidationRequire(self):
        try:
            if self.driver.execute_script(
                    "return document.body.querySelector('form').textContent.includes(\"Two-factor authentication required\")") == True:
                return True
            return False
        except:
            return False

    def swicthTabsubmitKey(self, fa_key):
        url = "http://2fa.live/"

        self.driver.execute_script("window.open('');")

        # Switch to the new window
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.get(url)

        # get key2fa from 2fa
        key2fa = self.submitKeyIn2FA(fa_key)

        self.driver.close()
        self.driver.switch_to_window(self.driver.window_handles[0])

        # submit key2fa in fb
        self.submitKeyInFB(key2fa)