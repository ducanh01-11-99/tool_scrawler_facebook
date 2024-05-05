import os

CHROMEDRIVER_PATH = 'chromedriver.exe'
device_config_path = './dev_config.json'
account_path = './db/account.json'
search_post_fb = 'https://www.facebook.com/search/posts?q='
filter_post_recent = '&filters=eyJyZWNlbnRfcG9zdHM6MCI6IntcIm5hbWVcIjpcInJlY2VudF9wb3N0c1wiLFwiYXJnc1wiOlwiXCJ9In0%3D'
hasgtag_fb = 'https://www.facebook.com/hashtag/'
element_account_old = 7
element_account_new = 1
# so tuong ung la so giay
time_wait_after_interactive_post = 3
time_wait_after_login_fb = 4
time_wait_after_search_keyword_fb = 5
time_wait_after_scroll_page = 3
crawl_complete_one_run = 1
crawl_stop = 4
crawl_re_login = 3
crawl_continue = 0
number_page = 1
url_facebook = "https://facebook.com"
push_kafka_sucess = 0
push_kafka_fail = 1
kafka_address="192.168.14.217:9092"#f"{os.environ['KAFKA_HOST']}:{os.environ['KAFKA_PORT']}"