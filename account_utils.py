import json
import time
import scraper
import config
from account import Account
from browser import WebBrowser


def check_login(brs):
    source = brs.get_source().decode('utf-8')
    source_scraper = scraper.Scraper(source)
    if source_scraper.soup.text.lower().find(
            "log in") != -1 and source_scraper.soup.text.lower().find(
        "create new account") != -1:
        return False


def check_is_account_locked(brs):
    source = brs.get_source().decode('utf-8')
    source_scraper = scraper.Scraper(source)
    if source_scraper.soup.text.lower().find(
            "your account has been disabled") != -1 or source_scraper.soup.text.lower().find(
        "your account has been locked") != -1:
        print("Tai khoan fb crawl da bi khoa-----")
        return False
    
    
def check_login(brs):
    source = brs.get_source().decode('utf-8')
    source_scraper = scraper.Scraper(source)
    if source_scraper.soup.text.lower().find(
            "log in") != -1 and source_scraper.soup.text.lower().find(
                "create new account") != -1:
        return False
    
    
def check_nick_die(brs):
    source = brs.get_source().decode('utf-8')
    source_scraper = scraper.Scraper(source)
    if source_scraper.soup.text.lower().find("your account has been disabled") != -1 or source_scraper.soup.text.lower().find("your account has been locked") != -1:
        print("Tai khoan fb crawl da bi khoa-----")
        return False


def get_cookie_from_account_fb(account):
    arrr = {}
    cookies_from_selenium = {}
    
    web_browser = WebBrowser(proxy=account.proxy)
    #HoangLM: get k2fa
    two_fa_code = account.two_fa_code
    k2fa = None
    if len(two_fa_code) > 0:
        if len(two_fa_code) == 6:
            k2fa = two_fa_code
        else:
            k2fa = web_browser.get_k2FA(two_fa_code)
            if len(k2fa) != 6:
                k2fa = None
    print("k2fa:", k2fa)
    web_browser.get_url(url=config.url_facebook)
    web_browser.login(account.username, account.password)
    time.sleep(config.time_wait_after_login_fb)
    print("aaaa:", web_browser.check2StepValidationRequire())
    if web_browser.check2StepValidationRequire() == True:
        web_browser.swicthTabsubmitKey(297327)
    if check_login(web_browser) == False:
        return ""
    elif check_nick_die(web_browser) == False:
        return ""
    #HoangLM: dang nhap bang 2fa
    if not k2fa is None:
        web_browser.submit_2fakey_to_fb(k2fa)
    list_cookie_from_selenium = web_browser.driver.get_cookies()
    for cookie in list_cookie_from_selenium:
        cookies_from_selenium[cookie['name']] = cookie['value']
    cookies = "Cookie: fr=" + cookies_from_selenium.get('fr') \
                        + "; sb=" + cookies_from_selenium.get('sb') \
                        + "; datr=" + cookies_from_selenium.get('datr') \
                        + "; wd=" + cookies_from_selenium.get('wd') \
                        + "; c_user=" + cookies_from_selenium.get('c_user') \
                        + "; xs=" + cookies_from_selenium.get('xs')
    web_browser.driver.close()
    return cookies


def read_and_convert_account_from_json(file_path):
    accounts = dict()
    try:
        with open(file_path, 'r') as fp:
            dict_cookies_open = json.load(fp)
        for key in dict_cookies_open:
            account = Account(key, dict_cookies_open[key]["password"], dict_cookies_open[key]["cookies"])
            accounts[key] = account
    except ValueError:
        print("file account empty!")
    return accounts

def get_local_account_list_from_json(file_path):
    local_accounts = {}
    
    try:
        with open(file_path,'r+') as f:
            local_accounts=json.load(f)
    except Exception as ex:
        print("Exception: File account db cua co du lieu!")
        
    return local_accounts


def update_account_to_local_json_file(account, file_path):
    accounts = read_and_convert_account_from_json(file_path)
    accounts[account.username] = account
    with open(file_path, 'w') as fp:
        json.dump(accounts, fp, default=lambda o: o.__dict__, sort_keys=True, indent=4)
    print("update account to json done!")


def write_account_list_to_local_db_file(local_account, file_path):
    with open(file_path, 'w') as fp:
        json.dump(local_account, fp, default=lambda o: o.__dict__, sort_keys=True, indent=4)
        
        
def delete_local_account(local_account, data):
    try:
        del local_account[data['account']['username']]
    except Exception as ex:
        print("Exception: loi xoa tai khoan", ex)