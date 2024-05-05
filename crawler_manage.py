import os
import json
from typing import List
import config
import device_config_utils
import crawler_manage_utils
from utils import utils
from account import Account
from crawler import CrawlerThread
from api.api_client import ApiClient
from wsclient.websocket_client import EventType
from wsclient.websocket_client import WebsocketClient
from account_utils import read_and_convert_account_from_json
import queue
import time
from utils.log_utils import logger

class CrawlerManager(object):
    crawler_process = dict()
    crawler_config = ""
    # local_accounts = {}#read_and_convert_account_from_json(file_path=config.account_path)
    crawler_threads = []
    local_accounts = read_and_convert_account_from_json(file_path=config.account_path)

    def __init__(self, device_config):
        self.ws_url = None
        self.ws = None
        self.ip = None
        #self.api_client = ApiClient()
        #self.work_websocket()
        print("CrawlerManager init")
        number_config = len(device_config)
        for i in range(number_config):
            # todo Tạo luồng theo số lượng tài khoản
            self.load_device_config_and_create_clawer_thread(device_config[i])
            
    
    def work_websocket(self):
        self.ws_url = "ws://192.168.14.217:8083/ws/device-server/"#os.environ['WS_HOST']
        self.ip = utils.get_ip_address()
        self.ws = WebsocketClient(url=self.ws_url + self.ip + "/", event_callback=self.on_websocket_event)
        self.ws.connect_background()
        

    def load_device_config_and_create_clawer_thread(self, config):
        #todo lấy thông tin tài khoản
        account = Account(config["account"]["username"], config["account"]["password"], "")
        array_data = config["account"]["platform"].split("+")
        if len(array_data) > 1:
            account.two_fa_code = config["account"]["platform"].split("+")[1]
        if len(array_data) > 2:
            account.proxy = config["account"]["platform"].split("+")[2]
        if account.username not in self.local_accounts:
            self.local_accounts[account.username] = account
        else:
            account = self.local_accounts[account.username]
        config['mode']['keyword_noparse'] = config['mode']['keyword']
        config['mode']['keyword'] = self.parse_keyword(keyword_list_raw=config['mode']['keyword'])
        self.create_and_run_crawler_thread(account=account, config=config)


    def parse_keyword(self, keyword_list_raw: str) -> List[str]:
        keyword_list_raw_dict = json.loads(keyword_list_raw)
        keyword_list: List[str] = []

        # Lặp qua mỗi dict trong danh sách
        for item in keyword_list_raw_dict:
            # Lấy giá trị của key
            key = item['key']
            
            # Lặp qua mỗi giá trị trong subKey
            for subkey in item['subKey']:
                # Tạo từ khóa kết hợp từ key và subKey
                combined_keyword = f"{key} {subkey}"
                # Thêm từ khóa kết hợp vào danh sách keywords
                keyword_list.append(combined_keyword)

        return keyword_list

        
    def create_and_run_crawler_thread(self, account, config):
        if int(config['mode']['id']) == 1: #mode search

            # todo Đặt hàng đợi có giá trị 100
            share_queue = queue.Queue(maxsize=100)

            crawler1 = CrawlerThread(account, config["account"]["platform"], mode=1, keywords=config["mode"]["keyword"], keyword_noparse=config["mode"]["keyword_noparse"], mode_search = "get_link", share_queue = share_queue)
            crawler1.setDaemon(True)
            crawler1.start()
            self.add_crawler(crawler1)

            time.sleep(20)

            crawler2 = CrawlerThread(account, config["account"]["platform"], mode=1, keywords=config["mode"]["keyword"], keyword_noparse=config["mode"]["keyword_noparse"], mode_search = "ex_post", share_queue = share_queue)
            crawler2.start()
            self.add_crawler(crawler2)
        elif int(config['mode']['id']) == 2: #mode get post group
            share_queue = queue.Queue(maxsize=100)

            #todo tạo luồng, lấy link các bài viết trong trang
            crawler1 = CrawlerThread(account, config["account"]["platform"], mode=2, mode_group = "get_link", group_id =config['mode']['group_id'], share_queue=share_queue)
            crawler1.setDaemon(True)

            #todo bắt đầu luồng
            crawler1.start()
            self.add_crawler(crawler1)

            time.sleep(20)

            crawler2 = CrawlerThread(account, config["account"]["platform"], mode=2, mode_group = "ex_post", group_id =config['mode']['group_id'], share_queue=share_queue)
            #crawler2.setDaemon(True)
            crawler2.start()
            #crawler2.run()
            self.add_crawler(crawler2)
        else:
            # giá trị ở đây lúc nào cũng là 3, do phần trên không update phần mode
            print("No mode")
            logger.error("No mode")


    def add_crawler(self, crawler):
        self.crawler_threads.append(crawler)
        
    def update_device_config_to_json(self, device_config, file_path):
        device_config_list = device_config_utils.get_local_device_config()
        device_config_list.append(device_config)
        with open(file_path, 'w') as fp:
            json.dump(device_config_list, fp, default=lambda o: o.__dict__, sort_keys=True, indent=4)
            
            
    def delete_device_config_and_account_from_ws(self, data):
        for crawler in self.crawler_threads:
            thread_name = crawler.thread_name
            usename_of_thread = thread_name.split('_')[1]
            if data['account']['username'] == usename_of_thread:
                crawler_manage_utils.delete_and_update_device_config(data=data)
                crawler_manage_utils.delete_and_update_account(data=data)
                self.local_accounts = read_and_convert_account_from_json(file_path=config.account_path)
                crawler_manage_utils.kill_clawer_thread(crawler=crawler, crawler_threads=self.crawler_threads)
                print("Da xoa tai khoan: ", usename_of_thread)
                
                
    def on_websocket_event(self, message_json):
        try:
            print("on_websocket_event", message_json)
            data = message_json['data']
            event = message_json['event']
            if event == EventType.connection_established:
                print("on_websocket_event Connection established")
            elif event == EventType.connection_error:
                print("on_websocket_event Connection error")
            elif event == EventType.connection_lost:
                print("on_websocket_event Connection lost")
            elif event == EventType.device_configure:
                print("on_websocket_event Device configure")
                self.update_device_config_to_json(data, config.device_config_path)
                self.load_device_config_and_create_clawer_thread(data)
            elif event == EventType.delete_configure:
                print("on_websocket_event Delete configure")
                self.delete_device_config_and_account_from_ws(data=data)
            else:
                print(f"on_websocket_event Unknown event {event} with data {data}")
        except Exception as e:
            print("Exception: websocket: ")
            print(f"on_websocket_event event = {event} data = {data} error = {e}")
